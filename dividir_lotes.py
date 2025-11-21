import pandas as pd
import os
import math

# --- CONFIGURAÇÕES ---
TAMANHO_LOTE = 1000  # Quantos leads por arquivo?
PASTA_SAIDA = 'Leads_Diarios' # Nome da pasta que será criada
PADRAO_ARQUIVO = 'Cosmeticos_ATIVAS_' # Prefixo dos arquivos que ele vai buscar

def dividir_arquivos():
    # 1. Cria a pasta de saída se não existir
    if not os.path.exists(PASTA_SAIDA):
        os.makedirs(PASTA_SAIDA)
        print(f"Pasta '{PASTA_SAIDA}' criada com sucesso.")
    
    # 2. Encontra os arquivos CSV na pasta atual
    arquivos_encontrados = [f for f in os.listdir('.') if f.startswith(PADRAO_ARQUIVO) and f.endswith('.csv')]
    
    if not arquivos_encontrados:
        print("Nenhum arquivo de lead encontrado! Verifique se o nome começa com 'Cosmeticos_ATIVAS_'.")
        return

    lote_global_contador = 1 # Para numerar sequencialmente (Lote 1, 2, 3...)

    for arquivo in arquivos_encontrados:
        print(f"\nProcessando arquivo matriz: {arquivo}...")
        
        # Lê o arquivo gigante
        # dtype=str garante que telefones e CNPJs não percam zeros ou virem notação científica
        df = pd.read_csv(arquivo, sep=';', encoding='utf-8-sig', dtype=str)
        
        total_linhas = len(df)
        total_lotes = math.ceil(total_linhas / TAMANHO_LOTE)
        
        print(f"   -> Total de leads: {total_linhas}")
        print(f"   -> Será dividido em {total_lotes} arquivos.")

        # Identifica se é Celular ou Fixo pelo nome do arquivo original para colocar no nome do lote
        tipo = "CELULAR" if "CELULAR" in arquivo.upper() else "FIXO"
        if "OUTROS" in arquivo.upper(): tipo = "OUTROS"

        # 3. Loop para fatiar
        for i in range(total_lotes):
            inicio = i * TAMANHO_LOTE
            fim = inicio + TAMANHO_LOTE
            
            # Pega o pedaço (slice) do dataframe
            df_lote = df.iloc[inicio:fim]
            
            # Define o nome do arquivo: Ex: Lote_001_CELULAR.csv
            nome_lote = f"Lote_{lote_global_contador:03d}_{tipo}.csv"
            caminho_completo = os.path.join(PASTA_SAIDA, nome_lote)
            
            # Salva
            df_lote.to_csv(caminho_completo, index=False, sep=';', encoding='utf-8-sig')
            
            lote_global_contador += 1
        
        print(f"   -> Concluído! Arquivos gerados para {arquivo}.")

    print(f"\n--- PROCESSO FINALIZADO ---")
    print(f"Todos os lotes estão na pasta: /{PASTA_SAIDA}")

if __name__ == "__main__":
    dividir_arquivos()