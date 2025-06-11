import random
import time
import pandas as pd
import numpy as np
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
import httpx
from lxml import html
from html2image import Html2Image

@dataclass
class artikel_info():
    """product_info"""
    ean: list[str]
    product_id: str

@dataclass
class artikel_compatablility_info():
    """product_info"""
    Merk: str
    Machinecode : str
    Apparaatnaam: str
    Type: str


website = "https://www.beekman.nl"
compatible_product_list, product_info = [], []

def get_compatible_products(link, first=True, multiple_letters=False):
    try:
        response = httpx.get(f"{website}{link}", timeout=10)
        time.sleep(0.5)  # Sleep to avoid overwhelming the server with requests
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        tree = html.fromstring(response.content)
        if first:
            ean = tree.xpath("//li[normalize-space()='EAN-nummer']/following-sibling::li/text()")
            product_id_raw = tree.xpath("//li[normalize-space()='Artikelnummer']/following-sibling::li/text()")
            if ean and product_id_raw:
                product_info.append(artikel_info(ean[0], product_id_raw[0].replace(".", "").replace("-", "")))
            else:
                print("EAN or product ID not found on the page.")
                return #Exit the function if no ean or product id is found

        merken = tree.xpath("//tbody//td[1]//text()")
        machinecode = tree.xpath("//tbody//td[3]//text()")
        apparaatnaams = tree.xpath("//tbody//td[4]//text()")
        types = tree.xpath("//tbody//td[5]//text()")

        for Merk, Machinecode, Apparaatnaam, Type in zip(merken, machinecode, apparaatnaams, types):
            compatible_product_list.append(artikel_compatablility_info(Merk.strip(),Machinecode.strip(), Apparaatnaam.strip(), Type.strip()))

        next_page_links = tree.xpath("//th[@class='is-next']/a/@href")
        if next_page_links:
            get_compatible_products(next_page_links[0], first=False,multiple_letters=multiple_letters)
        else:
            if not multiple_letters:
                meerdere_letters_active = tree.xpath("//ul[@class='startchars responsive-select float-left mb-4']//li[not(contains(concat(' ', @class, ' '), ' disabled ')) and not(contains(concat(' ', @class, ' '), ' active '))]/a/@href ")
                for letter_link in meerdere_letters_active:
                    get_compatible_products(letter_link, first=False,multiple_letters=True)
    except httpx.TimeoutException:
        print(f"Error: The read operation timed out for URL: {website}{link}. Server took too long to respond.")

def get_product_info():
    compatible_product_list.clear()
    product_info.clear()
    product_id_or_ean = product_number.get()
    search_response = httpx.get(f"{website}/zoeken?keyword={product_id_or_ean}")
    search_response.raise_for_status()
    search_tree = html.fromstring(search_response.content)
    link_product_pages = search_tree.xpath("//a[@class='productlink fluid']/@href")

    if link_product_pages:
        get_compatible_products(link_product_pages[0])
        product_df = pd.DataFrame(compatible_product_list)
        product_df_filterd_merk = product_df.assign(
            Merk=lambda x: np.where(x['Merk'] != x['Merk'].shift(), x['Merk'], np.nan),
            Apparaatnaam=lambda x: np.where(x['Apparaatnaam'] != x['Apparaatnaam'].shift(), x['Apparaatnaam'], np.nan)
        )
        product_df_filterd_merk.to_html(
            f"search_id-{product_id_or_ean}-beekman-ean-{product_info[0].ean}-product-id-{product_info[0].product_id}.html",
            na_rep="", justify="center", index=False
        )
        hti = Html2Image(size=(550, 1500), output_path='fotos')
        css = "body {background: white;}"
        hti.browser.use_new_headless = None 
        if product_df_filterd_merk.shape[0] < 50:
            hti.screenshot(
                html_str=product_df_filterd_merk.to_html(na_rep="", justify="center", index=False),
                css_str=css,
                save_as=f'{product_id_or_ean}.png'
            )
        else:
            product_df_filterd_merk_dict = {
                n: product_df_filterd_merk.iloc[n:n + 60, :]
                for n in range(0, len(product_df_filterd_merk), 60)
            }
            for count, value in enumerate(product_df_filterd_merk_dict.values(), start=1):
                hti.screenshot(
                    html_str=value.to_html(na_rep="", justify="center", index=False),
                    css_str=css,
                    save_as=f'{product_id_or_ean}_{count}.png',
                )
        product_number.delete(0, 'end')
    else:
        print("Product link not found.")

def change_button_color():
    colors = ["red", "green", "blue", "orange", "purple", "cyan", "magenta", "yellow"]
    random_color = random.choice(colors)
    generate_button.config(style=f"Colored.TButton")
    style.configure("Colored.TButton", background=random_color)


# Create application window
app = tk.Tk()
app.title("Product Compatibility Info")
app.geometry("400x100")

# entry field for user input
label = ttk.Label(app, text="Enter EAN or Product ID:")
label.pack()

product_number = ttk.Entry(app)
product_number.pack()

style = ttk.Style() #Create style object
style.configure("TButton", padding=5, font=('Arial', 10))

# Trigger the CSV generation
generate_button = ttk.Button(app, text="Generate CSV", command=get_product_info, style="TButton")
generate_button.pack()
app.bind("<Return>", lambda event=None: generate_button.invoke())

app.mainloop()
