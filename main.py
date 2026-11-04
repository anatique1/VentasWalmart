from src.extraction import extract_sales, extract_holidays


def main():
    sales = extract_sales()
    holidays_df = extract_holidays()
    print(sales.head(3))
    print(holidays_df.head(3))


if __name__ == "__main__":
    main()