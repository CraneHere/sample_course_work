from datetime import datetime

from repositories.sales import add_sale, add_sale_details
from pandas import DataFrame
import time


class SalesService:
    def process_sale(self, sale_date: datetime, items: DataFrame) -> int:
        # time.sleep(10)
        items = items.rename(columns={"Количество": "quantity", "Barcode": "barcode"})
        items = items.groupby("barcode", as_index=False)["quantity"].sum()
        sale_id = add_sale(sale_date)

        items["sale_id"] = sale_id
        add_sale_details(items)

        return sale_id
