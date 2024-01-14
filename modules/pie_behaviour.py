from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns

def generate_pie_behaviour(df):
    sum_column1 = df['Behaviour_Polite'].sum()
    sum_column2 = df['Behaviour_Abusive'].sum()
    sum_column3 = df['Behaviour_Rude'].sum()

    sum_values = [sum_column1, sum_column2, sum_column3]

    labels = ['Polite', 'Abusive', 'Rude']

    plt.figure(figsize=(6, 6))
    sns.set_palette("pastel")
    plt.pie(x=sum_values, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.title('Behaviour Distribution')
    
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)

    return img_buffer