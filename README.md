# 🏆 Speed Chess Championship 2024 — ML Prediction Model

Predicting the results of the [Speed Chess Championship 2024](https://www.chess.com/events/2024-speed-chess-championship-main-event) using **XGBoost** and **Monte Carlo simulation**.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Overview

The Speed Chess Championship (SCC) is Chess.com's premier online speed chess tournament featuring 16 of the world's best players. Each match consists of three segments: 5+1 blitz, 3+1 blitz, and 1+1 bullet, with the player scoring the most points advancing.

This project builds a machine learning pipeline that:
1. **Collects data** from the Chess.com API (ratings + 2,826 head-to-head games)
2. **Engineers features** from rating differences, H2H history, and ELO expected scores
3. **Trains an XGBoost model** to predict individual game outcomes
4. **Simulates full matches** using Monte Carlo methods (10,000 iterations per match)
5. **Predicts the entire tournament bracket** from Round 1 through the Final

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

**Overall Match Prediction Accuracy: 10/11 (90.9%)**

### Model Performance

| Metric | Value |
|--------|-------|
| Cross-validation Accuracy | 60.0% ± 5.6% |
| Training Samples | 2,291 decisive games |
| Features | 14 |
| Match-level Accuracy | 87.5% (Round 1) |

> **Note:** 60% accuracy on individual blitz/bullet games translates to 87%+ accuracy on full matches (39 games each) due to the Law of Large Numbers — variance decreases as sample size increases.

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

## Methodology

### Data Collection
- Player ratings via Chess.com Public API
- 2,826 blitz and bullet games between the 16 participants (Jan 2023 — Jul 2024)
- Head-to-head statistics for all player pairs

### Feature Engineering (14 features per matchup)
- **Rating differences:** blitz, bullet, best ratings
- **H2H winrates:** overall, blitz-specific, bullet-specific
- **H2H sample size:** total games, blitz games, bullet games
- **ELO expected score:** `E = 1 / (1 + 10^((Rb-Ra)/400))`
- **Average ratings:** overall match strength indicator

### Model
- **Algorithm:** XGBoost (Gradient Boosted Decision Trees)
- **Hyperparameters:** 200 trees, max_depth=4, learning_rate=0.05, L2 regularization
- **Validation:** 5-fold cross-validation

### Match Simulation
- Monte Carlo simulation with 10,000 iterations per match
- Match structure: 15 games (5+1 blitz) + 12 games (3+1 blitz) + 12 games (1+1 bullet)
- Tiebreak simulation included
- Draw rates calibrated per time control (15% blitz, 8% bullet)

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

## Known Limitations & Future Improvements

- **Overconfident predictions:** Some matches predicted at 99-100% due to small H2H sample sizes (e.g., only 3 games between Magnus and MVL)
- **Online ≠ Tournament:** Model trained on casual online games, but tournament conditions differ significantly
- **No historical SCC data:** Adding results from SCC 2017-2023 would improve predictions
- **Rating snapshots:** Using current ratings rather than ratings at time of each game

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
