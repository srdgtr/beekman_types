import pandas as pd
import numpy as np
from dataclasses import dataclass

import tkinter as tk
from tkinter import ttk

try:
    from requests_html import HTMLSession
except ModuleNotFoundError as ve:
    print(f"{ve} please run install_needed_files first")

try:
    from html2image import Html2Image
except ModuleNotFoundError as ve:
    print(f"{ve} please run install_needed_files first")

session = HTMLSession()

@dataclass
class artikel_info():
    """product_info"""
    ean: list[str]
    product_id: str

@dataclass
class artikel_compatablility_info():
    """product_info"""
    Merk: str
    Apparaatnaam: str
    Type : str

website = "https://www.beekman.nl"
compatible_product_list,product_info = [],[]

def get_compatible_products(link, first = True):
    page_body = session.get(f"{website}{link}").html
    if first:
        product_info.append(artikel_info(page_body.xpath("//li[normalize-space()='EAN-nummer']/following-sibling::li/text()")[0],page_body.xpath("//li[normalize-space()='Artikelnummer']/following-sibling::li/text()")[0].replace(".","").replace("-","")))

    for Merk, Apparaatnaam, Type in zip(page_body.xpath("//tbody//td[1]//text()"),page_body.xpath("//tbody//td[4]//text()"),page_body.xpath("//tbody//td[5]//text()")):
        compatible_product_list.append(artikel_compatablility_info(Merk.strip(), Apparaatnaam.strip(), Type.strip()))
    next_page_link = page_body.xpath("//th[@class='is-next']/a/@href")
    if next_page_link:
        get_compatible_products(next_page_link[0], first=False)

def get_product_info():
    compatible_product_list.clear()
    product_info.clear()
    product_id_or_ean = product_number.get()
    search_page = session.get(f"{website}/zoeken?keyword={product_id_or_ean}")
    link_product_page = search_page.html.xpath("//a[@class='productlink fluid']/@href")[0]
    get_compatible_products(f"{link_product_page}")
    product_df = pd.DataFrame(compatible_product_list)
    product_df_filterd_merk = product_df.assign(Merk= lambda x: np.where(x['Merk'] != x['Merk'].shift(), x['Merk'], np.nan),
                                                Apparaatnaam= lambda x: np.where(x['Apparaatnaam'] != x['Apparaatnaam'].shift(), x['Apparaatnaam'], np.nan))
    product_df_filterd_merk.to_html(f"search_id-{product_id_or_ean}-beekman-ean-{product_info[0].ean}-product-id-{product_info[0].product_id}.html", na_rep = "",justify="center", index=False)
    hti = Html2Image(size=(550, 1500))
    css = "body {background: white;}"
    if product_df_filterd_merk.shape[0] < 50:
        hti.screenshot(html_str=product_df_filterd_merk.to_html(na_rep = "",justify="center", index=False), css_str=css, save_as=f'{product_id_or_ean}.png')
    else:
        product_df_filterd_merk_dict = {n: product_df_filterd_merk.iloc[n:n+60, :] for n in range(0, len(product_df_filterd_merk), 60)}
        for count,value in enumerate(product_df_filterd_merk_dict.values(), start=1):
            hti.screenshot(
                html_str=value.to_html(
                    na_rep="", justify="center", index=False
                ),
                css_str=css,
                save_as=f'{product_id_or_ean}_{count}.png',
            )
    product_number.delete(0, 'end')


# Create application window
app = tk.Tk()
app.title("Product Compatibility Info")
app.geometry("400x100")

# entry field for user input
label = ttk.Label(app, text="Enter EAN or Product ID:")
label.pack()

product_number = ttk.Entry(app)
product_number.pack()

# Trigger the CSV generation
generate_button = ttk.Button(app, text="Generate CSV", command=get_product_info)
generate_button.pack()
app.bind("<Return>", lambda event=None: generate_button.invoke())
app.mainloop()

