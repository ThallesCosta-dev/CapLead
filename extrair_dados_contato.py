import pandas as pd
import os
import numpy as np

# --- CONFIGURAÇÕES ---
LISTA_ARQUIVOS = [
    'K3241.K03200Y0.D51108.ESTABELE', 
    'K3241.K03200Y1.D51108.ESTABELE',
    'K3241.K03200Y2.D51108.ESTABELE',
    'K3241.K03200Y3.D51108.ESTABELE',
    'K3241.K03200Y4.D51108.ESTABELE', 
    'K3241.K03200Y5.D51108.ESTABELE',
    'K3241.K03200Y6.D51108.ESTABELE',
    'K3241.K03200Y7.D51108.ESTABELE',
    'K3241.K03200Y8.D51108.ESTABELE',
    'K3241.K03200Y9.D51108.ESTABELE'
] 

LIMITE_EXCEL = 1000000 

# CNAEs alvo
CNAES_ALVO = ['4772500', '4646001']

# Colunas do Layout
COLUNAS = [
    'CNPJ_BASICO', 'CNPJ_ORDEM', 'CNPJ_DV', 'IDENTIFICADOR_MATRIZ_FILIAL', 
    'NOME_FANTASIA', 'SITUACAO_CADASTRAL', 'DATA_SITUACAO_CADASTRAL', 
    'MOTIVO_SITUACAO_CADASTRAL', 'NOME_CIDADE_EXTERIOR', 'PAIS', 
    'DATA_INICIO_ATIVIDADE', 'CNAE_FISCAL_PRINCIPAL', 'CNAE_FISCAL_SECUNDARIA',
    'TIPO_DE_LOGRADOURO', 'LOGRADOURO', 'NUMERO', 'COMPLEMENTO', 'BAIRRO',
    'CEP', 'UF', 'MUNICIPIO', 'DDD_1', 'TELEFONE_1', 'DDD_2', 'TELEFONE_2',
    'DDD_FAX', 'FAX', 'CORREIO_ELETRONICO', 'SITUACAO_ESPECIAL', 'DATA_SITUACAO_ESPECIAL'
]

# Controle Global
controle = {
    'FIXO': {'contador': 0, 'parte': 1},
    'CELULAR': {'contador': 0, 'parte': 1},
    'OUTROS': {'contador': 0, 'parte': 1}
}

def salvar_chunk(df, tipo):
    global controle
    if df.empty: return

    estado = controle[tipo]
    
    if estado['contador'] + len(df) > LIMITE_EXCEL:
        estado['parte'] += 1
        estado['contador'] = 0
        print(f"--- [AVISO] Arquivo {tipo} encheu! Criando Parte {estado['parte']} ---")

    nome_arquivo = f"Cosmeticos_ATIVAS_{tipo}_Parte{estado['parte']}.csv"
    
    header = (estado['contador'] == 0)
    mode = 'w' if header else 'a'
    
    # Salvando com separador ; e encoding utf-8-sig
    df.to_csv(nome_arquivo, mode=mode, index=False, header=header, sep=';', encoding='utf-8-sig')
    estado['contador'] += len(df)

def processar_dados():
    total_fixo = 0
    total_celular = 0
    
    for arquivo_atual in LISTA_ARQUIVOS:
        print(f"\n>>> Lendo arquivo: {arquivo_atual} <<<")
        
        if not os.path.exists(arquivo_atual):
            print(f"Aviso: {arquivo_atual} não encontrado. Pulando...")
            continue 

        reader = pd.read_csv(
            arquivo_atual, sep=';', encoding='latin-1', header=None, names=COLUNAS,
            dtype=str, chunksize=100000
        )

        for i, chunk in enumerate(reader):
            
            mask_cnae = chunk['CNAE_FISCAL_PRINCIPAL'].isin(CNAES_ALVO)
            mask_ativa = chunk['SITUACAO_CADASTRAL'] == '02'
            
            df = chunk[mask_cnae & mask_ativa].copy()

            if not df.empty:
                # Tratamentos
                df['CNPJ_COMPLETO'] = df['CNPJ_BASICO'] + df['CNPJ_ORDEM'] + df['CNPJ_DV']
                df['DDD_1'] = df['DDD_1'].fillna('')
                df['TELEFONE_1'] = df['TELEFONE_1'].fillna('').str.replace(r'\D', '', regex=True)

                df['TELEFONE_FORMATADO'] = df.apply(
                    lambda x: f"({x['DDD_1']}) {x['TELEFONE_1']}" if x['TELEFONE_1'] else "", axis=1
                )
                
                # --- AQUI ESTÁ A MUDANÇA: Adicionei 'UF' na seleção ---
                df_final = df[[
                    'NOME_FANTASIA', 
                    'CNPJ_COMPLETO', 
                    'UF',  # <--- Coluna Nova
                    'CNAE_FISCAL_PRINCIPAL', 
                    'CNAE_FISCAL_SECUNDARIA', 
                    'TELEFONE_1', 
                    'TELEFONE_FORMATADO', 
                    'CORREIO_ELETRONICO'
                ]].copy()
                
                # Renomeando as colunas
                df_final.columns = ['Nome', 'CNPJ', 'UF', 'CNAE Principal', 'CNAE Sec', 'Tel_Raw', 'Telefone', 'Email']

                # Lógica de Separação (Igual ao anterior)
                primeiro_digito = df_final['Tel_Raw'].str[0]
                primeiro_digito_num = pd.to_numeric(primeiro_digito, errors='coerce')

                mask_celular = (primeiro_digito_num >= 6)
                mask_fixo = (primeiro_digito_num >= 2) & (primeiro_digito_num <= 5)
                mask_outros = (~mask_celular) & (~mask_fixo)

                df_celular = df_final[mask_celular].drop(columns=['Tel_Raw'])
                df_fixo = df_final[mask_fixo].drop(columns=['Tel_Raw'])
                df_outros = df_final[mask_outros].drop(columns=['Tel_Raw'])

                salvar_chunk(df_fixo, 'FIXO')
                salvar_chunk(df_celular, 'CELULAR')
                salvar_chunk(df_outros, 'OUTROS')
                
                total_fixo += len(df_fixo)
                total_celular += len(df_celular)

            if i % 20 == 0:
                print(f"   Bloco {i}... Acumulado (Celular: {total_celular} | Fixo: {total_fixo})")

    print("\n--- CONCLUÍDO ---")
    print(f"Total ATIVAS Celulares: {total_celular}")
    print(f"Total ATIVAS Fixos: {total_fixo}")

if __name__ == "__main__":
    processar_dados()