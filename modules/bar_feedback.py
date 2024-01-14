from io import BytesIO
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

def generate_image(df):
    groupdf = df.groupby(['City']).sum()
    groupdf['City'] = groupdf.index
    melted_df = pd.melt(groupdf, id_vars=['City'], value_vars=['Negative_Feedback', 'Positive_Feedback'])
    sns.set(rc={"xtick.labelsize": 14, "ytick.labelsize": 14, "axes.labelsize": 16, "axes.titlesize": 18})
    plt.figure(figsize=(15, 20))
    ax = sns.barplot(x='value', y='City', hue='variable', data=melted_df, orient='h')
    for p in ax.patches:
        ax.annotate(f'{p.get_width():.2f}', (p.get_width(), p.get_y() + p.get_height() / 2),
                    ha='center', va='center', fontsize=10, color='black', xytext=(5, 0),
                    textcoords='offset points', weight='bold')
    plt.xlabel('Feedback Count')
    plt.ylabel('City', fontsize=14, fontweight='bold')
    plt.title('Negative and Positive Feedback by City')
    plt.tight_layout()

    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)

    return img_buffer