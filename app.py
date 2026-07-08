def render_pro_chart(symbol):
    df = yf.download(f"{symbol}.NS", period="6mo", interval="1d", progress=False)
    if df.empty: 
        st.warning(f"Data not available for {symbol}")
        return
    
    # --- FIX: Handle MultiIndex Columns if returned by yfinance ---
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1) # Drop the ticker level from columns
    
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    df['RSI'] = 100 - (100 / (1 + (avg_gain / (avg_loss + 1e-10))))

    # Multi-Panel Professional Chart Setup
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, 
                        row_width=[0.2, 0.2, 0.6])

    # 1. Candlestick Core Plot
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Candlestick"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], line=dict(color='#3b82f6', width=1.5), name="EMA 20"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='#f59e0b', width=1.5), name="EMA 50"), row=1, col=1)

    # 2. Volume Profile Subplot (FIXED: Direct vector comparison instead of iterrows loop)
    colors = ['#10b981' if c >= o else '#ef4444' for o, c in zip(df['Open'], df['Close'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name="Volume"), row=2, col=1)

    # 3. RSI Oscillators Subplot
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#a855f7', width=1.5), name="RSI"), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#10b981", row=3, col=1)

    # Premium Dark Styling layout adjustments
    fig.update_layout(template="plotly_dark", height=650, 
                      xaxis_rangeslider_visible=False,
                      margin=dict(l=10, r=10, t=30, b=10),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    
    fig.update_xaxes(showgrid=True, gridcolor='#1e293b')
    fig.update_yaxes(showgrid=True, gridcolor='#1e293b')
    st.plotly_chart(fig, use_container_width=True)
    
