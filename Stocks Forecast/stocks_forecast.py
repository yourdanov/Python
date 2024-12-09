import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Suppress TensorFlow INFO/WARNING logs
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"  # Disable oneDNN optimizations

import yfinance as yf
from datetime import datetime
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import tkinter as tk
from tkinter import Label, Button
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential # type: ignore
from tensorflow.keras.layers import LSTM, Dense, Dropout # type: ignore
from tensorflow.keras.callbacks import EarlyStopping # type: ignore
import tensorflow.keras.backend as K # type: ignore
from sklearn.preprocessing import MinMaxScaler
from statsmodels.tsa.stattools import adfuller
from pmdarima import auto_arima
from datetime import datetime
import matplotlib.dates
import mplcursors
import nltk

nltk.download("vader_lexicon", quiet=True)  # Suppress download message


# === 1. Fetch historical stocks data ===
def fetch_stock_data(stock_symbol, start_date, end_date):
    try:
        stock_data = yf.download(stock_symbol, start=start_date, end=end_date)
        stock_data.index = pd.to_datetime(stock_data.index, errors='coerce')  # Ensure datetime format for the index
        stock_data = stock_data['Close'].asfreq('ME', method='pad')  # Use month-end frequency
        stock_data.name = "Price"  # Name the series for clarity
        return stock_data
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return pd.Series(dtype=float)


# === 2. Forecast with ARIMA (AutoRegressive Integrated Moving Average) ===
def forecast_arima(stock_data, steps=12):
    try:
        # Ensure input data is valid
        stock_data = stock_data.dropna().astype(float)
        if stock_data.empty:
            print("No data available for ARIMA. Returning fallback values.")
            return pd.Series(
                [0] * steps, index=pd.date_range(start=datetime.now(), periods=steps, freq="ME")
            )

        # Ensure data is stationary
        stock_data_diff = stock_data.diff().dropna()
        if stock_data_diff.empty:
            print("Differenced data is empty. Returning fallback values.")
            return pd.Series(
                [0] * steps, index=pd.date_range(start=datetime.now(), periods=steps, freq="ME")
            )

        # Fit ARIMA model
        print("Fitting ARIMA model...")
        model = auto_arima(
            stock_data_diff,
            start_p=1, start_q=1,
            max_p=5, max_q=5,
            d=1, seasonal=False,
            stepwise=True, error_action="ignore",
            suppress_warnings=True, random_state=42
        )

        # Forecast future steps
        forecast_diff = model.predict(n_periods=steps)

        # Reverse differencing to get actual forecast
        last_value = stock_data.iloc[-1]
        forecast = [float(last_value) + sum(forecast_diff[:i+1]) for i in range(len(forecast_diff))]

        # Create date index
        future_dates = pd.date_range(start=datetime.now(), periods=steps, freq="ME")
        forecast_series = pd.Series(forecast, index=future_dates, name="ARIMA Forecast")

        print("ARIMA Forecast Values (processed):", forecast_series)

        return forecast_series
    except Exception as e:
        print(f"Error in ARIMA model: {e}")
        return pd.Series(
            [float(stock_data.iloc[-1])] * steps,
            index=pd.date_range(start=datetime.now(), periods=steps, freq="ME"),
            name="Fallback ARIMA"
        )


# === 3. Forecast with ETS (Exponential Smoothing) ===
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def forecast_ets(stock_data, steps=12):
    try:
        # Initialize variables to store the best model
        best_model = None
        best_aic = float('inf')
        best_params = None

        # Possible configurations for trend and seasonality
        configs = [
            {"trend": "add", "seasonal": "add"},
            {"trend": "mul", "seasonal": "mul"},
            {"trend": "add", "seasonal": "mul"},
            {"trend": "mul", "seasonal": "add"}
        ]

        # Grid search over trend and seasonal configurations
        for config in configs:
            try:
                model = ExponentialSmoothing(
                    stock_data,
                    seasonal=config["seasonal"],
                    seasonal_periods=12,
                    trend=config["trend"],
                    initialization_method="estimated"  # Use robust initialization
                )
                model_fit = model.fit()
                aic = model_fit.aic  # Akaike Information Criterion for model selection

                if aic < best_aic:
                    best_aic = aic
                    best_model = model_fit
                    best_params = config

            except Exception as e:
                print(f"Error with ETS config {config}: {e}")

        # Forecast using the best model
        if best_model:
            forecast = best_model.forecast(steps)
            forecast.index = pd.date_range(start=datetime.now(), periods=steps, freq='ME')
            print(f"Best ETS Model: Trend={best_params['trend']}, Seasonal={best_params['seasonal']}, AIC={best_aic}")
            return forecast
        else:
            print("No valid ETS model found. Falling back to default.")
            return pd.Series(
                [stock_data.iloc[-1]] * steps,
                index=pd.date_range(start=datetime.now(), periods=steps, freq='ME')
            )

    except Exception as e:
        print(f"Error in ETS model: {e}")
        return pd.Series(
            [stock_data.iloc[-1]] * steps,
            index=pd.date_range(start=datetime.now(), periods=steps, freq='ME')
        )


# === 4. Forecast with Random Forest ===
def forecast_random_forest(stock_data, steps=12):
    try:
        # Add lagged features and technical indicators
        stock_data = stock_data.reset_index()
        stock_data.columns = ["Date", "Price"]
        stock_data["Date"] = pd.to_datetime(stock_data["Date"])  # Ensure datetime format
        stock_data["Ordinal"] = stock_data["Date"].map(datetime.toordinal)
        stock_data["Lag_1"] = stock_data["Price"].shift(1)
        stock_data["Lag_7"] = stock_data["Price"].shift(7)
        stock_data["Lag_30"] = stock_data["Price"].shift(30)
        stock_data["SMA_7"] = stock_data["Price"].rolling(window=7).mean()
        stock_data["Volatility_7"] = stock_data["Price"].rolling(window=7).std()
        stock_data["Month"] = stock_data["Date"].dt.month
        stock_data["DayOfWeek"] = stock_data["Date"].dt.dayofweek

        stock_data.dropna(inplace=True)  # Drop rows with missing values

        # Prepare data
        feature_columns = ["Ordinal", "Lag_1", "Lag_7", "Lag_30", "SMA_7", "Volatility_7", "Month", "DayOfWeek"]
        X = stock_data[feature_columns]
        y = stock_data["Price"]

        X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train Random Forest
        model = RandomForestRegressor(n_estimators=300, max_depth=10, random_state=42)
        model.fit(X_train, y_train)

        # Predict future prices
        future_dates = [datetime.now() + pd.DateOffset(months=i) for i in range(1, steps + 1)]
        last_row = stock_data.iloc[-1]

        future_features = pd.DataFrame({
            "Ordinal": [date.toordinal() for date in future_dates],
            "Lag_1": [last_row["Price"]] + [np.nan] * (steps - 1),
            "Lag_7": [last_row["Lag_1"]] + [np.nan] * (steps - 1),
            "Lag_30": [last_row["Lag_7"]] + [np.nan] * (steps - 1),
            "SMA_7": [last_row["SMA_7"]] + [np.nan] * (steps - 1),
            "Volatility_7": [last_row["Volatility_7"]] + [np.nan] * (steps - 1),
            "Month": [date.month for date in future_dates],
            "DayOfWeek": [date.weekday() for date in future_dates],
        })

        # Fill future lagged features iteratively
        for i in range(1, steps):
            future_features.loc[i, "Lag_1"] = future_features.loc[i - 1, "Lag_1"]
            future_features.loc[i, "Lag_7"] = future_features.loc[max(i - 6, 0), "Lag_1"]
            future_features.loc[i, "Lag_30"] = future_features.loc[max(i - 29, 0), "Lag_1"]

        # Use ffill() to forward-fill missing values
        future_features = future_features.ffill()
        forecast = model.predict(future_features)

        return pd.Series(forecast, index=future_dates)
    except Exception as e:
        print(f"Error in Random Forest model: {e}")
        return pd.Series([stock_data.iloc[-1]] * steps, index=pd.date_range(start=datetime.now(), periods=steps, freq="ME"))


# === 5. Forecast with LSTM (Long Short-Term Memory) ===
def forecast_lstm(stock_data, steps=12):
    try:
        # Prepare data for LSTM
        data = stock_data.values.reshape(-1, 1)
        train_data = data[:-steps]

        # Normalize data
        from sklearn.preprocessing import MinMaxScaler
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(data)

        # Prepare sequences for training
        X_train, y_train = [], []
        for i in range(60, len(train_data)):
            X_train.append(scaled_data[i - 60:i, 0])  # 60 time steps as input
            y_train.append(scaled_data[i, 0])  # Target value

        X_train, y_train = np.array(X_train), np.array(y_train)
        X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

        # Build LSTM model
        model = Sequential([
            tf.keras.layers.Input(shape=(X_train.shape[1], 1)),  # Explicit Input layer
            LSTM(units=50, return_sequences=True),  # First LSTM layer with output sequences
            Dropout(0.2),  # Dropout to prevent overfitting
            LSTM(units=50),  # Second LSTM layer
            Dropout(0.2),  # Dropout to prevent overfitting
            Dense(units=1)  # Dense layer for output
        ])

        model.compile(optimizer="adam", loss="mean_squared_error")
        model.fit(X_train, y_train, epochs=50, batch_size=32, verbose=1)  # Train model with 50 epochs

        # Prepare data for predictions
        inputs = scaled_data[len(train_data) - 60:]  # Use the last 60 days of data for prediction
        X_test = []
        for i in range(60, len(inputs)):
            X_test.append(inputs[i - 60:i, 0])  # Create sequences for prediction

        X_test = np.array(X_test)
        X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

        # Generate predictions
        predictions = model.predict(X_test)
        predictions = scaler.inverse_transform(predictions)  # Transform predictions back to original scale

        # Create a forecast series
        future_dates = [datetime.now() + pd.DateOffset(months=i) for i in range(1, steps + 1)]
        return pd.Series(predictions.flatten(), index=future_dates)

    except Exception as e:
        print(f"Error in LSTM model: {e}")
        return pd.Series([stock_data.iloc[-1].item()] * steps, index=pd.date_range(start=datetime.now(), periods=steps, freq='ME'))


# === 6. Show Historical Data Graph ===
def show_historical_data_graph(root, stock_data):
    try:
        last_10_years = stock_data[stock_data.index >= pd.Timestamp(datetime.now() - pd.DateOffset(years=10))]
        if isinstance(last_10_years, pd.DataFrame):
            last_10_years = last_10_years.squeeze()

        graph_window = tk.Toplevel(root)
        graph_window.title("Historical Stock Data - Last 10 Years")
        graph_window.geometry("1200x800")

        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        ax.plot(last_10_years.index, last_10_years, label="Historical Data", color="blue")
        ax.set_title("IBM Historical Stock Prices - Last 10 Years", fontsize=16)
        ax.set_xlabel("Year", fontsize=14)
        ax.set_ylabel("Price (US $)", fontsize=14)
        ax.grid(True)
        ax.legend()

        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        toolbar = NavigationToolbar2Tk(canvas, graph_window)
        toolbar.update()
        toolbar.pack(side="top", fill="x")
    except Exception as e:
        print(f"Error displaying historical data graph: {e}")


# === 7. Create GUI ===
def create_gui(stock_data, current_price):
    root = tk.Tk()
    root.title("IBM Stocks Analysis Tool")
    root.geometry("1920x1080")
    root.configure(bg="#f0f0f0")

    # Set app icon
    try:
        root.iconbitmap("stocks.ico")
    except Exception:
        pass  # Fallback if the icon is missing

    # === Header Frame ===
    header_frame = tk.Frame(root, bg="#003366", height=100)
    header_frame.pack(fill="x")

    title_label = Label(
        header_frame,
        text="IBM Stocks Analysis and Forecasting",
        font=("Arial", 28, "bold"),
        bg="#003366",
        fg="white",
    )
    title_label.pack(pady=20)

    # === Current Info Frame ===
    info_frame = tk.Frame(root, bg="#e6f2ff", padx=10, pady=10)
    info_frame.pack(fill="x", pady=10)

    current_date_label = Label(
        info_frame,
        text=f"Current Date: {datetime.now().strftime('%Y-%m-%d')}",
        font=("Arial", 16),
        bg="#e6f2ff",
        fg="#003366",
    )
    current_date_label.pack(side="left", padx=20)

    current_price_label = Label(
        info_frame,
        text=f"Current Stock Price: ${current_price:.2f}",
        font=("Arial", 16),
        bg="#e6f2ff",
        fg="#003366",
    )
    current_price_label.pack(side="left", padx=20)

    # Main Content Frame
    content_frame = tk.Frame(root, bg="#f0f0f0")
    content_frame.pack(fill="both", expand=True)

    # Comparison Graph
    steps = 12
    forecast_arima_vals = forecast_arima(stock_data, steps)
    forecast_ets_vals = forecast_ets(stock_data, steps)
    forecast_rf_vals = forecast_random_forest(stock_data, steps)
    forecast_lstm_vals = forecast_lstm(stock_data, steps)

    fig, ax = plt.subplots(figsize=(12, 8), dpi=100)
    if not forecast_arima_vals.empty:
        ax.plot(forecast_arima_vals.index, forecast_arima_vals, label="ARIMA", marker="o")
    else:
        print("ARIMA forecast is empty or invalid. Skipping ARIMA plot.")
    ax.plot(forecast_ets_vals.index, forecast_ets_vals, label="ETS", marker="x")
    ax.plot(forecast_rf_vals.index, forecast_rf_vals, label="Random Forest", marker="s")
    ax.plot(forecast_lstm_vals.index, forecast_lstm_vals, label="LSTM", marker="^")
    ax.set_title("Comparison of Forecast Models", fontsize=16)
    ax.set_xlabel("Month", fontsize=14)
    ax.set_ylabel("Price (US$)", fontsize=14)
    ax.grid(True)
    ax.legend()

    canvas = FigureCanvasTkAgg(fig, master=content_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)

    # Add hover functionality
    def update_annotation(sel):
        try:
            # Convert numerical x-axis value to a date using Matplotlib's date converter
            hovered_date = matplotlib.dates.num2date(sel.target[0]).strftime('%Y-%m-%d')
            hovered_price = sel.target[1]  # y-axis value
            # Update annotation text
            sel.annotation.set_text(f"${hovered_price:,.2f} @ {hovered_date}")
        except Exception as e:
            print(f"Error adding hover functionality: {e}")

    # Connect hover functionality
    mplcursors.cursor(ax, hover=True).connect("add", update_annotation)

    # Button Frame
    button_frame = tk.Frame(root, bg="#f0f0f0")
    button_frame.pack(fill="x", pady=20)

    def on_hover(button, color):
        button["bg"] = color

    def on_leave(button, color):
        button["bg"] = color

    historical_graph_button = Button(
        button_frame,
        text="Show Historical Data Graph",
        command=lambda: show_historical_data_graph(root, stock_data),
        font=("Arial", 14),
        bg="#0066cc",
        fg="white",
        activebackground="#004080",
    )
    historical_graph_button.pack(side="left", padx=20)

    historical_graph_button.bind(
        "<Enter>", lambda e: on_hover(historical_graph_button, "#004080")
    )
    historical_graph_button.bind(
        "<Leave>", lambda e: on_leave(historical_graph_button, "#0066cc")
    )

    exit_button = Button(
        button_frame,
        text="Exit",
        command=root.quit,
        font=("Arial", 14),
        bg="#cc0000",
        fg="white",
        activebackground="#800000",
    )
    exit_button.pack(side="right", padx=20)

    exit_button.bind("<Enter>", lambda e: on_hover(exit_button, "#800000"))
    exit_button.bind("<Leave>", lambda e: on_leave(exit_button, "#cc0000"))

    root.mainloop()


# === 8. Main Program ===
if __name__ == "__main__":
    stock_symbol = "IBM"  # Define the stock symbol
    start_date = "2010-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")

    # Fetch historical data for graph and model forecasts
    stock_data = fetch_stock_data(stock_symbol, start_date, end_date)

    # Fetch real-time stock price using intraday data
    try:
        intraday_data = yf.download(stock_symbol, period="1d", interval="1m")  # Intraday data
        if not intraday_data.empty:
            current_price = intraday_data["Close"].iloc[-1]  # Get the latest 'Close' price
        else:
            print("No intraday data available. Using the last known historical price.")
            current_price = stock_data.iloc[-1] if not stock_data.empty else 0.0
    except Exception as e:
        print(f"Error fetching real-time price: {e}")
        current_price = stock_data.iloc[-1] if not stock_data.empty else 0.0

    # Ensure current_price is a scalar value
    current_price = current_price.item() if hasattr(current_price, "item") else float(current_price)

    # Launch GUI
    create_gui(stock_data, current_price)
