"""Construye el dataset final a partir de los datos intermedios.

Entradas: data/selected.csv y data/reviews.csv
Salida:   data/dataset.csv
"""
import pandas as pd
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

selected = pd.read_csv(DATA / "selected.csv")
reviews = pd.read_csv(DATA / "reviews.csv")

df = selected.merge(reviews, on="appid")

# Feature: proporcion de reviews positivas
df["reviews_ratio"] = df["total_positive"] / df["total_reviews"]

# Feature: fecha de lanzamiento y edad del juego en dias
df["release_date"] = pd.to_datetime(df["release_ts"], unit="s", errors="coerce")
df["age_days"] = (pd.Timestamp.now() - df["release_date"]).dt.days

# Feature: bucket de precio
bins = [0, 5, 10, 20, 30, 40, 50, float("inf")]
labels = ["<5", "5-10", "10-20", "20-30", "30-40", "40-50", "50+"]
df["bucket"] = pd.cut(df["msrp"], bins=bins, labels=labels, right=False)

# Sacar ruido: juegos con muy pocas reviews
df = df[df["total_reviews"] >= 50]

df.to_csv(DATA / "dataset.csv", index=False)
print(f"dataset final: {len(df)} juegos -> {DATA / 'dataset.csv'}")