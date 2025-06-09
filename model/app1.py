from flask import Flask, request, render_template_string, jsonify
import joblib

app = Flask(__name__)
model = joblib.load('fraud_model2.pkl')  # Your trained LinearRegression model

# HTML form with result
html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Fraud Detection</title>
</head>
<body>
    <h2>Fraud Detection System</h2>
    <form method="POST">
        <label for="avg_transaction">Enter Average Transaction Value:</label>
        <input type="number" name="avg_transaction" required>
        <input type="submit" value="Check">
    </form>

    {% if result %}
        <h3>Prediction: {{ result }}</h3>
        <p>Business Rule: {{ rule }}</p>
        <p>Model Output (Regression Score): {{ prob }}</p>
        <p>Model Prediction: {{ model }}</p>
    {% endif %}
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    result = rule = model_pred = prob = None

    if request.method == 'POST':
        try:
            avg_transaction = float(request.form['avg_transaction'])

            # Business rule
            rule = 1 if avg_transaction > 26500 else 0

            # Model prediction (regression score, then threshold at 0.5)
            model_score = model.predict([[avg_transaction]])[0]
            model_pred = 1 if model_score >= 0.5 else 0

            # Final output message
            if avg_transaction > 26500:
                result = "Fraudulent (Business Rule)"
            else:
                result = "Fraudulent" if model_pred == 1 else "Not Fraudulent"

            return render_template_string(html, result=result, rule=rule,
                                          prob=round(model_score, 4), model=model_pred)

        except Exception as e:
            result = f"Error: {str(e)}"
            return render_template_string(html, result=result)

    return render_template_string(html)

if __name__ == '__main__':
    app.run(debug=True)
