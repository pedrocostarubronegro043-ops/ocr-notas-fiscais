import cv2
import pytesseract
import numpy as np
import pandas as pd
import re

# --- Configuração do Pytesseract ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- Configuração dos arquivos ---
# Use o nome da sua imagem CORTADA
img_original_path = 'bianotafiscal.png' # <- Mude para o nome da sua imagem CORTADA
img_saida_path = 'resultado_final_cortado.png'


def extrair_tabela_de_dados(img_para_tesseract):
    """
    Usa 'image_to_data' para extrair o layout e montar a tabela de itens.
    Esta versão implementa a lógica de "capturar tudo" (botar a mais),
    sem exigir um preço no final da linha.
    """
    print("\nIniciando extração de dados com image_to_data...")
    
    config_tesseract = '-l por --psm 4' 
    data = pytesseract.image_to_data(img_para_tesseract, config=config_tesseract, output_type=pytesseract.Output.DICT)
    
    # Regex para preços (ex: 6.89 ou 0.09)
    regex_preco_final = re.compile(r'^\d+[.,]\d{2}$')
    
    # Agrupar palavras por linha
    linhas = {}
    n_palavras = len(data['text'])
    for i in range(n_palavras):
        if int(data['conf'][i]) > 40 and data['text'][i].strip():
            key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
            palavra = data['text'][i]
            posicao_left = data['left'][i]
            if key not in linhas:
                linhas[key] = []
            linhas[key].append((palavra, posicao_left))

    # --- Bloco de Debug (Mantido) ---
    print("\n" + "="*30)
    print("   DEBUG: LINHAS BRUTAS DO TESSERACT")
    print("="*30)
    linhas_brutas_para_processar = []
    for key in sorted(linhas.keys()):
        palavras_na_linha = linhas[key]
        palavras_na_linha.sort(key=lambda x: x[1])
        palavras = [p[0] for p in palavras_na_linha]
        linhas_brutas_para_processar.append(palavras)
        print(f"Linha {key[-1]}: {' '.join(palavras)}")
    print("="*30 + "\n")
    # --- Fim do Debug ---

    # --- Processar as linhas ---
    itens_encontrados = []
    print("Iniciando processamento e limpeza das linhas...")

    # Filtro de lixo: Linhas que NÃO são itens
    palavras_chave_excluir = [
        'TOTAL', 'SUBTOTAL', 'PAGO', 'TROCO', 'DEBITO', 'CRÉDITO',
        'CARTÃO', 'FORMA', 'PAGAMENTO', 'LEI', 'TRIBUTOS', 'FEDERAL',
        'QTDE.', 'CÓDIGO', 'DESCRIÇÃO', 'DOCUMENTO', 'AUXILIAR'
    ]

    for palavras in linhas_brutas_para_processar:
        
        if not palavras:
            continue
            
        texto_da_linha = " ".join(palavras)

        # 1. PULA A LINHA SE FOR LIXO
        if any(ex in texto_da_linha.upper() for ex in palavras_chave_excluir):
            continue

        # 2. ENCONTRA O INÍCIO DO NOME
        # (Encontra a PRIMEIRA palavra que começa com uma LETRA)
        indice_inicio_nome = -1
        for i, p in enumerate(palavras):
            if p and p[0].isalpha(): 
                indice_inicio_nome = i
                break
        
        # Se não achou nenhuma palavra de nome, pula.
        if indice_inicio_nome == -1:
            continue
            
        # 3. PEGA O NOME E TENTA PEGAR O PREÇO
        preco = "VERIFICAR" # Valor padrão se o preço falhar
        palavras_do_nome = []

        # Checa se a última palavra é um preço
        if regex_preco_final.match(palavras[-1]):
            preco = palavras[-1]
            # Pega tudo do início do nome ATÉ a penúltima palavra
            palavras_do_nome = palavras[indice_inicio_nome:-1]
        else:
            # Se não terminou com preço (ex: LAVA ROUPAS)
            # Pega TUDO do início do nome até o fim
            palavras_do_nome = palavras[indice_inicio_nome:]

        descricao_limpa = " ".join(palavras_do_nome)
        
        # Adiciona à lista (sem mais filtros severos)
        if descricao_limpa:
            itens_encontrados.append({
                'Produto': descricao_limpa.strip(),
                'Valor': preco
            })

    if not itens_encontrados:
        print("Nenhum item foi encontrado.")
        return None

    # 4. Criar e retornar a tabela (DataFrame)
    df = pd.DataFrame(itens_encontrados)
    return df

def pipeline_corte_manual(caminho_imagem_cortada, caminho_imagem_saida):
    """
    Pipeline simplificado que assume que a imagem já foi cortada
    manualmente pelo usuário.
    
    Esta versão usa Otsu (para delimitar) e uma DILATAÇÃO VERTICAL
    (para engrossar o texto fino sem juntar as letras).
    """
    
    # 1. Carregar a imagem (já cortada)
    img_cortada = cv2.imread(caminho_imagem_cortada)
    if img_cortada is None:
        print(f"Erro: Não foi possível carregar '{caminho_imagem_cortada}'.")
        return
    print("Imagem cortada carregada.")

    # 2. Converter para Tons de Cinza
    img_cinza = cv2.cvtColor(img_cortada, cv2.COLOR_BGR2GRAY)

    # 3. Aplicar "Zoom" (Dobrar o tamanho)
    img_ampliada = cv2.resize(img_cinza, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    print("Imagem ampliada para melhorar a leitura do Tesseract.")
    
    # 4. Limpeza de Ruído (Opcional, mas bom antes do Otsu)
    img_com_blur = cv2.medianBlur(img_ampliada, 3)

    # 5. Binarização de Otsu (Para "delimitar bem cada letra")
    ret, img_otsu = cv2.threshold(
        img_com_blur,
        0,
        255,
        cv2.THRESH_BINARY | cv2.THRESH_OTSU
    )
    print(f"Binarização de Otsu aplicada. Limiar encontrado: {ret}")

    # --- 6. NOVO PASSO: Dilatação Vertical (para "engrossar" sem "juntar") ---
    
    # Inverte a imagem (Otsu nos dá texto preto 0, fundo branco 255)
    # Dilate funciona em pixels brancos.
    img_invertida = cv2.bitwise_not(img_otsu)

    # Criamos um KERNEL VERTICAL (1 pixel de largura, 2 pixels de altura)
    kernel_vertical = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 2))
    
    # Aplicamos a dilatação
    img_dilatada = cv2.dilate(img_invertida, kernel_vertical, iterations=1)
    
    # Desinverte para o Tesseract (texto preto, fundo branco)
    img_final_para_tesseract = cv2.bitwise_not(img_dilatada)
    
    print("Dilatação vertical aplicada para 'engrossar' o texto.")
    # --- Fim do Novo Passo ---
    
    # Salva a imagem final que o Tesseract vai ler
    cv2.imwrite(caminho_imagem_saida, img_final_para_tesseract)
    
    # 7. EXTRAIR OS DADOS
    tabela_de_itens = extrair_tabela_de_dados(img_final_para_tesseract)
    
    if tabela_de_itens is not None:
        print("\n" + "="*30)
        print("   TABELA DE ITENS EXTRAÍDA")
        print("="*30)
        print(tabela_de_itens)
        
        # Salva no Excel
        nome_arquivo_excel = "notas_fiscais_extraidas.xlsx"
        tabela_de_itens.to_excel(nome_arquivo_excel, index=False)
        print(f"\n[+] Tabela salva com sucesso como '{nome_arquivo_excel}'")
            
    else:
        print("\nNão foi possível extrair a tabela de itens.")

    # 8. Visualização
    cv2.imshow('1 - Imagem (Dilatada Vertical) p/ Tesseract', cv2.resize(img_final_para_tesseract, (600, 800), interpolation=cv2.INTER_AREA))
    cv2.waitKey(0)
    cv2.destroyAllWindows()
if __name__ == "__main__":
    # Certifique-se de ter o pandas instalado: pip install pandas openpyxl
    pipeline_corte_manual(img_original_path, img_saida_path)