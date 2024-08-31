import pandas as pd

from cotacoes import Cotacoes

if __name__ == "__main__":
    df = pd.read_parquet("dados/cotacoes.parquet")
    cotacoes = Cotacoes(df)
    cotacoes.atualizar_indicadores()
    cotacoes.salvar_cotacoes()
