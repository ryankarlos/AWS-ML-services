import pandas as pd
import os


df = pd.read_csv(
    "datasets/fraud-sample-data/dataset1/fraudTest.csv",
    dtype={"cc_num": "str"},
    parse_dates=[1],
)


start = pd.to_datetime("2020-06-21")
end = pd.to_datetime("2020-12-31")
# then filter out anything not inside the specified date ranges:
df = df[(start <= df.trans_date_trans_time) & (df.trans_date_trans_time <= end)]

# use only CARD_BIN from the credit card information
df["cc_num"] = df["cc_num"].str[:5]
# replace 0 with legit and 1 with fraud for our labels.
df["is_fraud"] = df["is_fraud"].replace({0: "legit", 1: "fraud"})

# rename columns to match mandatory field name for AWS service
df = df.rename(
    columns={"trans_date_trans_time": "EVENT_TIMESTAMP", "is_fraud": "EVENT_LABEL"}
)

fraud_samples = df.loc[df["EVENT_LABEL"] == "fraud", :].sample(5, axis=0)
legit_samples = df.loc[df["EVENT_LABEL"] == "legit", :].sample(70, axis=0)

# create concatenated df from sampled fraud and legit rows and then shuffle rows
df = pd.concat([legit_samples, fraud_samples]).sample(frac=1)

df["ENTITY_TYPE"] = "customer"
df["ENTITY_ID"] = "unknown"
df["EVENT_ID"] = df["trans_num"]

df.drop(
    [
        "Unnamed: 0",
        "merch_lat",
        "merch_long",
        "lat",
        "long",
        "unix_time",
        "dob",
        "EVENT_LABEL",
    ],
    axis=1,
    inplace=True,
)


df.to_csv("datasets/fraud-sample-data/dataset1/fraudTest_2020.csv", index=False)
