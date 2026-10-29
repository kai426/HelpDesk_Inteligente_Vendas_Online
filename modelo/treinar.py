"""
FASE 1 — Treino do modelo de Machine Learning.

O modelo aprende a CATEGORIA da dúvida do cliente (login, pagamento, entrega...),
usando o Pipeline do enunciado:
    TfidfVectorizer  ->  transforma texto em números
    MultinomialNB    ->  algoritmo Naive Bayes de classificação

A PRIORIDADE (baixa/media/alta/critica) é derivada da categoria por uma regra de
negócio (ver servicos/classificador.py). Fazemos assim porque, nesta base, a
prioridade depende da categoria, não do texto em si: pagamento é sempre "alta",
cancelamento é sempre "critica" etc. Treinar um classificador de texto para prever
a prioridade diretamente daria um resultado ruim e sem sentido.

O que este script produz:
  - modelo/modelo_categoria.pkl        -> modelo treinado (usado pela API)
  - relatorio/metricas.txt             -> acurácia + relatório por classe (para o relatório)
  - relatorio/matriz_confusao.png      -> imagem da matriz de confusão (para o relatório)

Rode assim (dentro da pasta do projeto, após gerar a base):
    python modelo/treinar.py
"""

import os
import joblib
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay

import matplotlib
matplotlib.use("Agg")  # permite salvar imagem sem abrir janela
import matplotlib.pyplot as plt

# Caminhos
PASTA_MODELO = os.path.dirname(os.path.abspath(__file__))
PASTA_PROJETO = os.path.dirname(PASTA_MODELO)
CSV = os.path.join(PASTA_PROJETO, "dados", "chamados.csv")
PASTA_RELATORIO = os.path.join(PASTA_PROJETO, "relatorio")
ARQ_CATEGORIA = os.path.join(PASTA_MODELO, "modelo_categoria.pkl")
ARQ_METRICAS = os.path.join(PASTA_RELATORIO, "metricas.txt")
ARQ_MATRIZ = os.path.join(PASTA_RELATORIO, "matriz_confusao.png")


def novo_pipeline() -> Pipeline:
    """Cria o pipeline Tfidf + Naive Bayes.

    ngram_range=(1,2) faz o modelo olhar palavras isoladas E pares de palavras
    (ex.: 'aguardando pagamento'), o que ajuda bastante em frases curtas.
    """
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
        ("clf", MultinomialNB()),
    ])


def main():
    if not os.path.exists(CSV):
        raise SystemExit(
            f"Não encontrei {CSV}.\n"
            f"Rode antes:  python dados/gerar_base.py"
        )
    os.makedirs(PASTA_RELATORIO, exist_ok=True)

    df = pd.read_csv(CSV)
    print(f"Base carregada: {len(df)} chamados, {df['categoria'].nunique()} categorias.")

    X = df["mensagem"]
    y = df["categoria"]

    # Separa parte dos dados para teste (para medir a acurácia de forma honesta).
    # stratify mantém a proporção de cada classe no treino e no teste.
    X_treino, X_teste, y_treino, y_teste = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    modelo = novo_pipeline()
    modelo.fit(X_treino, y_treino)

    # Avaliação
    y_prev = modelo.predict(X_teste)
    acc = accuracy_score(y_teste, y_prev)
    relatorio_txt = classification_report(y_teste, y_prev, zero_division=0)
    rotulos = sorted(y.unique())

    print("\n" + "=" * 60)
    print("MODELO DE CATEGORIA")
    print("=" * 60)
    print(f"Acurácia no conjunto de teste: {acc:.2%}")
    print("\nRelatório por classe:")
    print(relatorio_txt)

    # Salva as métricas em texto (para colar no relatório)
    with open(ARQ_METRICAS, "w", encoding="utf-8") as f:
        f.write("MÉTRICAS DO MODELO DE CATEGORIA (Fase 1)\n")
        f.write("=" * 50 + "\n")
        f.write(f"Base: {len(df)} chamados, {df['categoria'].nunique()} categorias.\n")
        f.write(f"Treino: {len(X_treino)} exemplos | Teste: {len(X_teste)} exemplos\n\n")
        f.write(f"Acurácia no conjunto de teste: {acc:.2%}\n\n")
        f.write("Relatório por classe:\n")
        f.write(relatorio_txt + "\n")

    # Salva a matriz de confusão como imagem
    fig, ax = plt.subplots(figsize=(9, 8))
    ConfusionMatrixDisplay.from_predictions(
        y_teste, y_prev, labels=rotulos, xticks_rotation=45, ax=ax, cmap="Blues", colorbar=False
    )
    ax.set_title("Matriz de Confusão — Classificação de Categoria")
    plt.tight_layout()
    fig.savefig(ARQ_MATRIZ, dpi=130)
    plt.close(fig)

    # Retreina com TODOS os dados antes de salvar (aproveita 100% da base).
    modelo_final = novo_pipeline()
    modelo_final.fit(X, y)
    joblib.dump(modelo_final, ARQ_CATEGORIA)

    print("\n" + "=" * 60)
    print("Arquivos gerados:")
    print(f"  - modelo:  {ARQ_CATEGORIA}")
    print(f"  - métricas: {ARQ_METRICAS}")
    print(f"  - matriz de confusão: {ARQ_MATRIZ}")
    print("=" * 60)


if __name__ == "__main__":
    main()
