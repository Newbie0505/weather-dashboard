import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import sqlite3

df = pd.read_sql(
    "SELECT * FROM weather_records ORDER BY timestamp DESC LIMIT 50",
    sqlite3.connect("data/weather.db")
)
df["timestamp"] = pd.to_datetime(df["timestamp"])
city = df["city"].iloc[0]
print(f"Found {len(df)} records for {city}")

sns.set_theme(style="darkgrid")
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle(f"Weather Report - {city}", fontsize=18, fontweight="bold")

axes[0,0].plot(df["timestamp"], df["temperature"], color="blue", marker="o")
axes[0,0].set_title("Temperature Over Time")
axes[0,0].tick_params(axis="x", rotation=45)

axes[0,1].bar(range(len(df)), df["humidity"], color="green")
axes[0,1].set_title("Humidity Levels")

cols = ["temperature","humidity","pressure","wind_speed"]
sns.heatmap(df[cols].corr(), annot=True, fmt=".2f", cmap="RdBu", ax=axes[1,0])
axes[1,0].set_title("Correlation Heatmap")

sns.histplot(df["wind_speed"], bins=10, kde=True, color="purple", ax=axes[1,1])
axes[1,1].set_title("Wind Speed Distribution")

plt.tight_layout()
plt.savefig("data/weather_report.png", dpi=150)
print("Report saved to data/weather_report.png")
plt.show()