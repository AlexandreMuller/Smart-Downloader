# Smart Downloader

## Descrição
O **Smart Downloader** é uma aplicação experimental e intuitiva para gerenciar downloads de arquivos diretamente da web. Este programa foi desenvolvido como um projeto de aprendizado e oferece uma interface amigável e recursos avançados, como:

- Resolução automática de URLs.
- Exibição de progresso, velocidade e tempo restante do download.
- Cancelamento de downloads em andamento.
- Histórico de downloads com informações detalhadas.
- Integração com navegadores para capturar links automaticamente.

## Funcionalidades

### 1. **Gerenciamento de Downloads**
- Adicione novos downloads manualmente ou via integração com o navegador.
- Visualize o progresso em tempo real com barra de progresso e informações detalhadas.
- Cancele downloads em andamento com um clique.

### 2. **Histórico de Downloads**
- Acompanhe os downloads realizados com informações como:
  - Nome do arquivo.
  - Tamanho total e baixado.
  - Velocidade média.
  - Tempo restante.
  - Local de salvamento.
  - Data e hora do download.

### 3. **Configurações Personalizáveis**
- Escolha o diretório padrão para salvar os arquivos.
- Histórico persistente salvo em `settings.ini`.

### 4. **Integração com Navegadores**
- Receba links diretamente do navegador via escutador de porta.

## Instalação

1. Certifique-se de ter o Python instalado (versão 3.8 ou superior).
2. Instale as dependências necessárias:

```bash
pip install -r requirements.txt
```

3. Execute o programa:

```bash
python main.py
```

## Como Usar

### 1. **Adicionar um Novo Download**
- Clique no botão **Novo Download**.
- Insira a URL do arquivo e escolha o diretório de salvamento.
- Clique em **Baixar** para iniciar o download.

### 2. **Cancelar um Download**
- Durante o download, clique no botão **Cancelar** ao lado do progresso.

### 3. **Limpar Histórico**
- Clique no botão **Limpar Histórico** para remover todos os downloads registrados.

### 4. **Receber Links do Navegador**
- Configure seu navegador para enviar links para o programa (porta 8080).

## Estrutura do Projeto

```
Smart Downloader/
├── main.py                # Arquivo principal da aplicação
├── download_widget.py     # Lógica do widget de download
├── interface.py           # Interface principal
├── settings.ini           # Configurações salvas
├── downloads/             # Diretório padrão para downloads
├── extensao/              # Extensão para navegador
│   ├── my-browser-extension/
│   │   ├── background.js
│   │   ├── content.js
│   │   ├── manifest.json
│   │   ├── popup.html
│   │   └── popup.js
```

## Contribuição
Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença
Este projeto está licenciado sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.