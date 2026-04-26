# 🏆 Speed Chess Championship 2024 — ML Prediction Model

Predicting the results of the [Speed Chess Championship 2024](https://www.chess.com/events/2024-speed-chess-championship-main-event) using **XGBoost** and **Monte Carlo simulation**.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Results

### Round 1 Predictions vs Actual Results

| Match | Prediction | Actual | Result |
|-------|-----------|--------|--------|
| Magnus Carlsen vs Tuan Minh Le | Magnus (99.9%) | Magnus 20.5 - 3.5 | ✅ |
| Duda vs Arjun Erigaisi | Arjun (60.3%) | Arjun 12 - 10 | ✅ |
| Wesley So vs Denis Lazavik | Wesley (91.5%) | Wesley 12 - 10 | ✅ |
| MVL vs Hans Niemann | MVL (67.9%) | Niemann 12.5 - 11.5 | ❌ |
| Hikaru vs Jose Martinez | Hikaru (100%) | Hikaru 14 - 8 | ✅ |
| Nepomniachtchi vs Abdusattorov | Nepo (76.3%) | Nepo 13 - 11 | ✅ |
| Firouzja vs Grischuk | Firouzja (77.8%) | Firouzja 13.5 - 10.5 | ✅ |
| Caruana vs Sarana | Caruana (97.9%) | Caruana 15 - 8 | ✅ |

**Round 1 Accuracy: 7/8 (87.5%)**

### Quarterfinal Predictions vs Actual

| Match | Prediction | Actual | Result |
|-------|-----------|--------|--------|
| Magnus vs Arjun | Magnus (100%) | Magnus 12 - 9 | ✅ |
| Hikaru vs Nepo | Hikaru (100%) | Hikaru 14.5 - 9.5 | ✅ |
| Firouzja vs Caruana | Firouzja (100%) | Firouzja 14.5 - 8.5 | ✅ |

**Overall Match Prediction Accuracy for 2 rounds: 10/11 (90.9%)**

### Model Performance

| Metric | Value |
|--------|-------|
| Cross-validation Accuracy | 60.0% ± 5.6% |
| Training Samples | 2,291 decisive games |
| Features | 14 |
| Match-level Accuracy | 87.5% (Round 1) |

> **Note:** 60% accuracy on individual blitz,bullet games translates to 87%+ accuracy on full matches (39 games each) due to the Law of Large Numbers — variance decreases as sample size increases.

## Feature Importance

The model found that **head-to-head history** is far more predictive than raw ratings:

```
h2h_winrate_all           37.4%  ██████████████████
h2h_winrate_blitz          8.4%  ████
h2h_winrate_bullet         6.1%  ███
h2h_games_total            5.6%  ██
elo_expected_bullet        5.0%  ██
elo_expected_blitz         4.8%  ██
blitz_diff                 3.1%  █
bullet_diff                3.7%  █
```

## Project Structure

```
speed-chess-prediction/
├── README.md
├── requirements.txt
├── LICENSE
├── notebooks/
│   └── scc_prediction.ipynb      # Main analysis notebook
├── src/
│   └── predict.py                # Core prediction functions
├── data/
│   ├── players_ratings.csv       # Player ratings
│   └── h2h_games.csv             # Head-to-head game history
└── results/
    └── tournament_predictions.txt # Full bracket predictions
```

## Quick Start

```bash
# Clone the repository
git clone https://github.com/SpectrumGM/speed-chess-prediction.git
cd speed-chess-prediction

# Install dependencies
pip install -r requirements.txt

# Run the notebook
jupyter notebook notebooks/scc_prediction.ipynb
```


## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
