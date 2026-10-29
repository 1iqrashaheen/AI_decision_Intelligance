# Business Decision Intelligence & Actionable Recommendations

**Prepared by:** Ahsan Rafique (AI Engineer)
**Project:** AI Decision Intelligence & What-If Simulator
**Task:** Future Sales Forecasting & Strategic Recommendations
**Evaluation Benchmark:** Random Forest Regressor vs. 7-Day Moving Average Baseline

---

## 1. Executive Summary
- **Predicted 30-Day Sales Revenue:** **£1,000,422.79**
- **Average Daily Expected Revenue:** **£33,347.43 / day**
- **Peak Revenue Day Expected:** **2012-01-04 (Wednesday)** with estimated **£53,864.56**
- **Lowest Operational Day Expected:** **2011-12-18 (Sunday)** with estimated **£18,182.29**
- **Model Reliability:** Random Forest achieved **£11,029.04 MAE**, outperforming the baseline by **47.12%**.

---

## 2. Weekly Demand Patterns & Operational Insights
Based on both historical data analysis and model feature importances:
- **Zero-Sales Pattern on Saturdays:** The retail transaction system consistently registers zero order processing on Saturdays. Operations and warehouse dispatch teams should align shifts accordingly.
- **Mid-Week / Thursday Peak:** Weekly sales consistently peak towards Thursdays and Wednesdays (Average expected: £45,943.29).
- **Weekend / Sunday Recovery:** Sunday resumes operations with moderate volumes (Average expected: £22,507.42).

---

## 3. Actionable Business Recommendations

### 📦 A. Inventory & Supply Chain Planning
1. **Stock Replenishment Timing:** Pre-buffer inventory on Tuesday and Wednesday mornings to meet the Thursday-Friday surge without stockouts.
2. **Weekend Buffer:** Minimize incoming supplier shipments on Saturday, scheduling major logistics deliveries for Monday and Tuesday.

### 💰 B. Marketing & Promotion Scheduling
1. **Targeted Campaigns:** Schedule marketing emails and promotional offers on Monday and Tuesday to drive the midweek buying momentum.
2. **Slow Day Stimulus:** Run limited-time flash discounts on lower-volume operational days (such as Sundays) to stimulate demand.

### 🔄 C. Return & Cancellation Risk Mitigation
1. **Net Revenue Monitoring:** The model uses **Net Sales Revenue** (accounting for customer cancellations and product returns). High gross days should maintain a 5–8% return reserve margin.
2. **High-Value Order Verification:** Introduce immediate automated fraud and order verification on large orders to reduce cancellation spikes.

---

## 4. Model Performance & Evaluation Proof
| Metric | 7-Day Moving Avg Baseline | Random Forest Regressor | Improvement |
| :--- | :--- | :--- | :--- |
| **MAE (Mean Absolute Error)** | £20,857.05 | **£11,029.04** | **+47.12% Better** |
| **RMSE** | £26,637.56 | **£17,439.71** | **+34.53% Better** |
| **R² Score** | N/A | **0.549** | High Predictive Power |

*Testing conducted chronologically on the final 30 days without data leakage.*
