# Quantitative Factor Backtesting on the China A-Share Market

## Author

**Wang Lei**

I am a dedicated and aspiring researcher with a strong background in quantitative finance, actively seeking a PhD position. This repository documents a systematic investigation into the efficacy of various risk and return factors within the China A-share market, showcasing my skills in empirical analysis, programming, and quantitative modeling.

---

## 1. Project Overview

This project presents a comprehensive backtesting analysis of several quantitative factors on the CSI 1000 Index constituent stocks. The primary objective is to empirically evaluate the performance and predictive power of these factors in the context of the Chinese A-share market.

The methodology involves:
- **Data Acquisition**: Daily market data is automatically collected and maintained.
- **Factor Construction**: A series of factors, primarily focusing on price-volume dynamics, risk metrics, and return distribution characteristics, were constructed.
- **Systematic Backtesting**: A rigorous backtesting framework was implemented using `backtrader` to simulate factor-based investment strategies.
- **Performance Analysis**: The results were systematically evaluated using standard quantitative metrics and visualizations.

---

## 2. Factors Investigated

The factors analyzed in this study are primarily derived from price and volume data. They can be broadly categorized as follows:

- **Risk Factors**:
  - **Dimson Beta**: Beta estimation adjusted for non-synchronous trading.
  - **Value at Risk (VaR)**: A measure of potential loss in value of a portfolio over a defined period for a given confidence interval.
  - **Conditional Value at Risk (CVaR)**: Also known as Expected Shortfall (ES), measures the expected loss on a portfolio in the worst-case scenarios.
  - **Tail Beta**: Measures the sensitivity of an asset to market movements during periods of extreme market stress.
  - **Tail Risk**: General measures quantifying the risk of extreme negative returns.

- **Return Distribution & Momentum Factors**:
  - **2-Month Highest Return**: A momentum factor based on the highest return over the past two months.
  - **Lowest Daily Return in Last 2 Months**: A factor capturing short-term reversal or extreme negative momentum.
  - **Total Skewness**: Measures the asymmetry of the entire return distribution.
  - **Idiosyncratic Skewness**: The skewness of returns not explained by market movements.
  - **Negative Skewness Coefficient**: A specific measure focusing on downside risk.
  - **Price Lag**: A factor capturing delayed price reactions.

- **Composite Factors**:
  - **Price-Volume Correlation**: A factor combining price and volume information.
  - **Index with Convertible Bonds**: A custom factor incorporating information from the convertible bond market.

---

## 3. Repository Structure and Methodology

The repository is organized into several key components, reflecting the workflow of the research.

- **`Factor Backtesting Tools.zip`**:
  - This archive contains the core backtesting logic implemented using the **`backtrader`** framework. It includes scripts for strategy definition, portfolio construction, and execution of the backtests.

- **`Calendar Datas pkl.zip`**:
  - This archive stores the prepared market and factor data in `.pkl` (pickle) format. This format ensures efficient data loading and processing during the backtesting phase.

- **`Factor Backtesting Reports.zip`**:
  - This archive contains detailed performance reports for each factor in Microsoft Word format. The reports provide a comprehensive analysis, including:
    - **Performance Metrics**: Annualized Cumulative Return, Max Drawdown, Annualized Volatility, and Sharpe Ratio.
    - **Visualizations**: Heatmaps of monthly returns, Q-Q plots to analyze return distributions, and other relevant charts.

- **`Daily Market Data Updater.py`**:
  - This is a standalone, scheduled script responsible for the automated collection of daily End-of-Day (EOD) closing prices for China A-shares. This ensures that the dataset remains current for ongoing analysis.

---

## 4. How to Use

1.  **Unzip Archives**: Decompress the `.zip` files to access the source code, data, and reports.
2.  **Review Code**: The backtesting logic can be reviewed in the `Factor Backtesting Tools` directory.
3.  **Examine Results**: The final performance analysis and visualizations for each factor can be found in the `Factor Backtesting Reports` directory.

**Note**: Due to the proprietary nature of the factor data and to maintain a reasonable repository size, the raw datasets are not included. However, the structure and methodology are fully documented.

## Contact

For any inquiries regarding the methodology, results, or potential academic collaborations, please feel free to contact me at: **[2823115764@qq.com]**
