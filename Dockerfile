# =============================================================================
# DOCKERFILE — Focus Log API
# =============================================================================
# Um Dockerfile é uma "receita" para criar uma imagem Docker.
# A imagem é um ambiente completamente isolado que contém tudo
# que a aplicação precisa para rodar: Python, dependências, código.
#
# Vantagem: "Funciona na minha máquina" nunca mais é um problema.
# =============================================================================

# Imagem base: Python 3.12 versão slim (menor, mais segura)
FROM python:3.12-slim

# Metadados da imagem
LABEL maintainer="seu@email.com"
LABEL description="Focus Log API — Backend de produtividade"

# =============================================================================
# VARIÁVEIS DE AMBIENTE DO CONTAINER
# =============================================================================

# PYTHONDONTWRITEBYTECODE: não gera arquivos .pyc (desnecessários no container)
ENV PYTHONDONTWRITEBYTECODE=1

# PYTHONUNBUFFERED: saída do Python vai direto para o terminal (sem buffer)
# Importante para ver logs em tempo real
ENV PYTHONUNBUFFERED=1

# =============================================================================
# CRIAR USUÁRIO NÃO-ROOT (segurança)
# =============================================================================
# Boa prática: nunca rodar a aplicação como root no container.
# Se a aplicação for comprometida, o invasor não tem poderes de root.

RUN addgroup --system appgroup && \
    adduser --system --group appuser

# =============================================================================
# DIRETÓRIO DE TRABALHO
# =============================================================================

WORKDIR /app

# =============================================================================
# INSTALAR DEPENDÊNCIAS
# =============================================================================
# Copiamos APENAS o requirements.txt primeiro para aproveitar o cache do Docker.
# Se o código mudar mas as dependências não, o Docker não reinstala tudo.

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# COPIAR O CÓDIGO
# =============================================================================

COPY . .

# Ajustar permissões para o usuário da aplicação
RUN chown -R appuser:appgroup /app

# Mudar para o usuário não-root
USER appuser

# =============================================================================
# EXPOR PORTA E COMANDO PADRÃO
# =============================================================================

EXPOSE 8000

# Comando para iniciar a aplicação
# Em produção, usaria gunicorn com workers múltiplos
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
