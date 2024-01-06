import os
import json
from io import BytesIO
from flask import Flask, Response, request
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
from supabase_py import create_client
from dotenv import load_dotenv
from flask_mail import Mail, Message


app = Flask(__name__)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'rajasthanhackathon4@gmail.com'
app.config['MAIL_PASSWORD'] = os.getenv('PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

plt.switch_backend('Agg')

load_dotenv()  # Load variables from the .env file

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    return 'Hellogi'


@app.route('/fetch_data', methods=['GET'])
def fetch_data():
    # Replace 'your_table_name' with the actual name of your Supabase table
    table_name = 'visits'

    # Fetch all rows from the specified table
    response = supabase.table(table_name).select().execute()

    # Get the rows from the response
    rows = response['data']

    df = pd.DataFrame(rows)

    # Create a new column 'Feeling' based on positive/negative values
    df['Feeling'] = df['Feel'].apply(lambda x: 'positive' if x > 0 else 'negative')

    # Group by 'policeStation' and count occurrences of each feeling
    grouped_data = df.groupby(['policeStation', 'Feeling']).size().unstack(fill_value=0).reset_index()

    # Rename columns for better clarity
    grouped_data.columns = ['policeStation', 'Negative Feel', 'Positive Feel']
    
    try:
        # Check if 'send_email' parameter is present in the URL
        send_email_param = request.args.get('send_email', '').lower()
        
        if send_email_param == 'true':
            pdf_bytes = plot_grouped_bar_chart_as_pdf(grouped_data)
            mailme(pdf_bytes)
        
        result = {'status': 'OK', 'data': grouped_data.to_dict(orient='records')}
    except Exception as e:
        result = {'status': 'FAILED', 'error': str(e)}
    
    response_json = json.dumps(result, ensure_ascii=False)
    return Response(response_json, content_type='application/json; charset=utf-8')



def plot_grouped_bar_chart_as_pdf(data):
    # Plotting the grouped bar chart
    fig, ax = plt.subplots(figsize=(10, 6))

    data.plot(kind='bar', x='policeStation', stacked=True, ax=ax)

    # Adding labels and title
    ax.set_xlabel('Police Station')
    ax.set_ylabel('Count')
    ax.set_title('Negative and Positive Feelings by Police Station')

    # Display the legend
    ax.legend(title='Feelings', loc='upper right')

    # Save the plot as a PDF in memory
    pdf_bytes = BytesIO()
    with PdfPages(pdf_bytes) as pdf:
        pdf.savefig(fig, bbox_inches='tight')

    # Close the plot to free up resources
    plt.close()

    return pdf_bytes.getvalue()

def mailme(pdf_bytes):
    all_emails = ['rajasthanhackathon4@gmail.com']
    with app.app_context():
        with mail.connect() as conn:
            for email in all_emails:
                message = 'A small gist of how was the perfomance of Rajasthan Police Stations'
                subject = "Monthly Rajasthan Police Station Report"
                msg = Message(recipients=[email],sender = 'Harsh Varshney',\
                            body=message,subject=subject)
                msg.attach("report.pdf", 'application/pdf', pdf_bytes)
                
                conn.send(msg)
    return "OK"

if __name__ == '__main__':
    app.run(debug=True)