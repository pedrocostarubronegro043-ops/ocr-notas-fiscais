# OCR de Notas Fiscais (NFC-e) 🧾

Um pipeline de Visão Computacional e OCR (Reconhecimento Óptico de Caracteres) desenvolvido em Python para extrair dados de produtos e preços de imagens de cupons fiscais brasileiros e exportá-los para Excel.

## 🎯 O Problema
Digitalizar notas fiscais manualmente é lento e propenso a erros. As notas fiscais (especialmente fotos de celular) apresentam desafios como:
* Iluminação irregular e sombras.
* Texto pequeno ou "embaçado".
* Ruído na impressão (pontos, falhas).
* Variações no layout dos itens.

## 🚀 A Solução
Este projeto automatiza a extração focando na **precisão dos dados**. Ele assume que o usuário fornece uma imagem contendo a área de interesse (lista de itens) e aplica um processamento agressivo para garantir que o OCR consiga ler até as letras mais finas.

### Principais Funcionalidades:
* **Pré-processamento de Imagem:** Conversão para escala de cinza e **Upscaling (Zoom 2x)** para melhorar a legibilidade de fontes pequenas.
* **OCR Robusto:** Utilização do **Tesseract OCR** com configurações otimizadas (`--psm 4`) para leitura de colunas.
* **Extração Inteligente:** Algoritmo personalizado em Python que utiliza **Regex** para identificar preços e isolar nomes de produtos, ignorando códigos e metadados irrelevantes.
* **Exportação Automática:** Gera uma planilha `.xlsx` pronta para uso.

## 🛠️ Tecnologias Utilizadas

* **Python 3.12+**
* **OpenCV (`cv2`):** Manipulação e tratamento de imagem.
* **Pytesseract:** Wrapper para o motor Tesseract OCR.
* **Pandas:** Estruturação e exportação de dados (DataFrame).
* **Regex (`re`):** Padrões de busca para limpeza de texto.

## ⚙️ Como Configurar

### 1. Pré-requisitos
Você precisa ter o **Tesseract-OCR** instalado no seu sistema (não apenas a biblioteca Python).
* **Windows:** [Baixe o instalador aqui](https://github.com/UB-Mannheim/tesseract/wiki).
* **Linux:** `sudo apt install tesseract-ocr tesseract-ocr-por`

### 2. Instalação
Clone o repositório e instale as dependências:

```bash
git clone [https://github.com/SEU_USUARIO/ocr-notas-fiscais.git](https://github.com/SEU_USUARIO/ocr-notas-fiscais.git)
cd ocr-notas-fiscais
pip install -r requirements.txt
