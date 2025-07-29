# Download Interceptor - Extensão do Navegador

Esta extensão intercepta downloads do navegador e os redireciona para o aplicativo downloader Python, **bloqueando completamente os pop-ups padrão de download do navegador**.

## ✨ Funcionalidades Principais

### 🚫 Bloqueio Total de Pop-ups de Download
- **Interceptação imediata**: Downloads são cancelados antes que o pop-up apareça
- **Remoção do histórico**: Downloads cancelados são removidos da lista do navegador
- **Múltiplas camadas**: Diferentes métodos garantem que nada escape

### 🎯 Interceptação Inteligente
- **API Downloads**: Intercepta downloads via `chrome.downloads.onCreated` e `onDeterminingFilename`
- **Content Script**: Intercepta cliques em links antes mesmo do download iniciar
- **Navegação**: Detecta redirecionamentos para URLs de download
- **Blob URLs**: Intercepta downloads gerados por JavaScript

### 🔍 Detecção Avançada
A extensão detecta downloads baseado em:
- **Extensões**: .zip, .exe, .pdf, .mp4, .mp3, .docx, .xlsx, etc.
- **Palavras-chave**: download, attachment, files, dl, force-download
- **Padrões de URL**: Reconhece estruturas típicas de URLs de download

## 📥 Como Instalar

1. Abra o Chrome e vá para `chrome://extensions/`
2. Ative o **"Modo do desenvolvedor"** no canto superior direito
3. Clique em **"Carregar sem compactação"**
4. Selecione a pasta `my-browser-extension`
5. A extensão será instalada e ativada automaticamente

## 🚀 Como Usar

1. **Execute o downloader**: `python main.py` (servidor na porta 8080)
2. **Navegue normalmente**: Clique em qualquer link de download
3. **Zero pop-ups**: O navegador não mostrará janelas de download
4. **Interface personalizada**: Sua janela de download aparecerá automaticamente

## ⚙️ Controles

- **Ícone da extensão**: Clique para ativar/desativar
- **Status visual**: Cores diferentes indicam se está ativo
- **Notificações**: Alertas quando o app local não está disponível

## 🛠️ Resolução de Problemas

### Downloads ainda aparecem no navegador
1. ✅ Verifique se a extensão está ativada (ícone colorido)
2. ✅ Confirme que o aplicativo Python está rodando
3. ✅ Recarregue a página e teste novamente
4. ✅ Alguns sites especiais podem contornar a interceptação

### Aplicativo não recebe URLs
1. ✅ Confirme que `main.py` está executando
2. ✅ Verifique se a porta 8080 não está bloqueada
3. ✅ Veja os logs no console do navegador (F12)

### Como desativar temporariamente
- Clique no ícone da extensão para desativar
- Ou desative em `chrome://extensions/`

## 📋 Tipos de Arquivo Suportados

### Arquivos Compactados
`.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.bz2`

### Executáveis e Instaladores  
`.exe`, `.msi`, `.dmg`, `.pkg`, `.deb`, `.rpm`, `.app`

### Documentos
`.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`

### Mídia
`.mp3`, `.wav`, `.mp4`, `.avi`, `.mkv`, `.mov`, `.jpg`, `.png`

### Outros
`.iso`, `.img`, `.bin`, `.apk`, `.ipa`, `.txt`, `.csv`, `.json`

## 🔒 Segurança e Privacidade

- ✅ **Apenas redirecionamento local**: URLs vão apenas para localhost:8080
- ✅ **Nenhum dado coletado**: Não armazena ou transmite informações pessoais  
- ✅ **Código aberto**: Todos os arquivos são visíveis e auditáveis
- ✅ **Permissões mínimas**: Usa apenas as permissões necessárias

## 🎉 Resultado Final

Com essas melhorias, você terá:
- **Zero pop-ups de download do navegador**
- **Interceptação confiável de todos os tipos de download**
- **Interface consistente através do seu aplicativo**
- **Experiência de download unificada e personalizada**