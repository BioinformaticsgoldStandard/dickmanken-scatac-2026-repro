# -----------------------------------------------------------
# 1. Immagine base: Jupyter + Python 3.10
# -----------------------------------------------------------
FROM jupyter/datascience-notebook:python-3.10

# -----------------------------------------------------------
# 2. Sezione ROOT: installazione strumenti di sistema + Docker
# -----------------------------------------------------------
USER root

# Install dipendenze di sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    wget curl git unzip build-essential \
    samtools bedtools bwa picard \
    ca-certificates gnupg lsb-release \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ---- Installazione di Docker Engine (DinD) ----
# Aggiungi la chiave GPG ufficiale di Docker e il repository
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Installa Docker Engine, CLI e containerd
RUN apt-get update && apt-get install -y --no-install-recommends \
    docker-ce docker-ce-cli containerd.io \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Aggiungi l'utente jovyan al gruppo docker (così non serve sudo)
RUN usermod -aG docker jovyan

# ---- Installazione MACS2 (via pip) ----
RUN pip install --no-cache-dir macs2==2.2.9.1

# ---- Installazione Nextflow ----
RUN wget -qO- https://get.nextflow.io | bash \
    && chmod +x nextflow \
    && mv nextflow /usr/local/bin/

# -----------------------------------------------------------
# 3. Sezione USER (jovyan): pacchetti Python e tool specifici
# -----------------------------------------------------------
USER jovyan

# pycisTopic v2.0a0 (alpha, da GitHub, con bug fix)
RUN git clone https://github.com/aertslab/pycisTopic.git /home/jovyan/pycisTopic \
    && cd /home/jovyan/pycisTopic \
    && sed -i 's/\.group_by(by="CB", maintain_order=True)/\.group_by("CB", maintain_order=True)/' src/pycisTopic/fragments.py \
    && pip install -e /home/jovyan/pycisTopic

# PUMATAC v0.0.1
RUN git clone --branch v0.0.1 https://github.com/aertslab/PUMATAC.git /home/jovyan/PUMATAC

# Altri pacchetti Python con versioni specifiche 
RUN pip install --no-cache-dir \
    pyBigWig==0.3.25 \
    deeptools==3.5.7 \
    ipywidgets==8.1.0 \
    pandas==2.0.3 \
    numpy==1.24.3 \
    scikit-learn==1.3.0 \
    matplotlib==3.7.2 \
    seaborn==0.12.2

# -----------------------------------------------------------
# 4. Entrypoint: avvia Docker interno e poi Jupyter
# -----------------------------------------------------------
WORKDIR /home/jovyan/work

# Copia lo script di entrypoint
COPY --chown=jovyan:users entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8888

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
