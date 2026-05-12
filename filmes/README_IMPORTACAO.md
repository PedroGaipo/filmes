# 📊 Importação de Filmes via Excel

## Como usar

1. **Acesse a funcionalidade**: Clique no botão "📊 Importar Excel" na barra lateral
2. **Prepare sua planilha**: Crie um arquivo Excel (.xlsx ou .xls) com os seguintes formatos:

### Formato da Planilha

**Coluna obrigatória:**
- `titulo`: Nome do filme (será usado para buscar na TMDB)

**Colunas opcionais:**
- `nota`: Nota de 0 a 10 (número decimal)
- `categoria`: Categorias separadas por vírgula (ex: "Drama, Ação")
- `comentario`: Seu comentário/review do filme

### Exemplo de Planilha

| titulo | nota | categoria | comentario |
|--------|------|-----------|------------|
| Interestelar | 9.5 | Ficção Científica, Drama | Filme incrível sobre espaço e tempo |
| O Poderoso Chefão | 10.0 | Drama, Crime | Clássico absoluto |
| Pulp Fiction | 9.2 | Crime, Suspense | Direção brilhante de Tarantino |

## O que acontece

1. **Upload**: O arquivo é enviado para o servidor
2. **Processamento**: Cada linha é processada:
   - Busca automática na TMDB usando o título
   - Dados da planilha sobrescrevem dados da TMDB quando disponíveis
3. **Validação**: Filmes não encontrados são reportados como erros
4. **Importação**: Filmes válidos são adicionados ao banco de dados
5. **Relatório**: Você recebe um resumo do que foi importado

## Arquivo de Exemplo

Um arquivo `exemplo_filmes.xlsx` foi criado na pasta do projeto com dados de exemplo para você testar.

## Notas Técnicas

- Arquivos aceitos: .xlsx e .xls
- Tamanho máximo: Depende da configuração do servidor
- Codificação: UTF-8 recomendada
- Filmes duplicados: Serão adicionados normalmente (não há verificação de duplicatas)