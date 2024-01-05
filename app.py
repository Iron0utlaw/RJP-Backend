import os
from io import BytesIO
from flask import Flask, send_file
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
from supabase_py import create_client
from dotenv import load_dotenv


app = Flask(__name__)

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
    
    pdf_bytes = plot_grouped_bar_chart_as_pdf(grouped_data)

    # Use BytesIO to create a file-like object for download
    pdf_file = BytesIO(pdf_bytes)

    # Send the file for download with a specified filename
    return send_file(pdf_file, download_name='grouped_bar_chart.pdf', as_attachment=True)


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

if __name__ == '__main__':
    app.run(debug=True)