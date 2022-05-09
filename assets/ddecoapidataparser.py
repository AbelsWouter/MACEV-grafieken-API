import pandas as pd
import numpy as np
import requests

# ***
# File: dataparser_ddeco.py
# Author: Wouter Abels (wouter.abels@rws.nl)
# Created: 16/06/21
# Last modified: 06/07/2021
# Python ver: 3.9.5
# ***

class dataparser:

    # Initialize class to save a API url as variable
    # Args: api_url (str, optional): Standard API url for querying. Defaults to None
    def __init__(self,
                 api_url: str):
        self.api_url = api_url

    #  Function to check HTTP error from API
    #  Args: e (requests.status_codes, optional): HTTP error from API. Defaults to None
    #  Returns: Bool: return True for break in while loop.
    def http_error_check(self,
                         e: requests.status_codes) -> bool:
        if e.response.status_codes == 403:
            print('Invalid api key')
            return True
        else:
            print(f'Error: {e.reason}')
            return True

    #  Builds query url for every page with defined endpoint, filters and skip properties
    #  Args:  query_url (str): API endpoint for query
    #         query_filter (str, optional): Filtering within API. Defaults to None.
    #         skip_properties (str, optional): Properties to skip in response. Defaults to None.
    #         page_number (int, optional): Starting page number. Defaults to 1.
    #         page_size (int, optional): Default max page size. Defaults to 10000.
    # Returns: str: [description]
    def url_builder(self,
                    query_url: str,
                    query_filter: str = None,
                    skip_properties: str = None,
                    page_number: int = 1,
                    page_size: int = 10000000) -> str:
        base = f'{self.api_url+query_url}?page={page_number}&pagesize={page_size}'
        if query_filter != None:
            base = f'{base}&filter={query_filter}'
        if skip_properties !=None:
            base = f'{base}&skipproperties={skip_properties}'
        base = base.replace(" ", "%20")
        return base

    # Check if ending of the response pages is reached (Response size smaller than max page size)
    # Args: response (list,optional: Response list from query. Defaults to None.
    #       page_size (int, optional): Max page size. Defaults to None
    def check_ending(self,
                     response: list,
                     page_size: int) -> bool:
        if len(response) < page_size:
            return True
        else:
            return False

    # Returns query from api, for testing and discovery purposes, Returns json result.
    # Args: query_url (str): API endpoint for query
    #       query_filter (str, optional): Filtering within API. Defaults to None.
    #       skip_properties (str, optional): Properties to skip in response. Defaults to None.
    #       api_key (str, optional): API key for identification as company. Defaults to None.
    #       page_number (int, optional): Starting page number. Defaults to 1.
    #       page_size (int, optional): Default max page size. Defaults to 10000.
    # Returns: listL reutrn query result
    def return_query(self,
                     query_url: str,
                     query_filter: str = None,
                     skip_properties: str = None,
                     api_key: str = None,
                     page: int = 1,
                     page_size: int = 1000000) -> list:

        request_url = self.url_builder(
            query_url, query_filter, skip_properties, page, page_size)
        try:
            request = requests.get(
                request_url, headers={"Accept": "application/json", "x-api-key": api_key}).json()
            return request["result"]
        except requests.HTTPError as e:
            self.http_error_check(e)

    # Parse through all pages and send to path file location as csv.
    # Args: api_key (str, optional): API key for identification as company. Defaults to None.
    #       query_url (str): API endpoint for query
    #       query_filter (str, optional): Filtering within API. Defaults to None.
    #       skip_properties (str, optional): Properties to skip in response. Defaults to None.
    #       page (int, optional): Starting page number. Defaults to 1.
    #       page_size (int, optional): Default max page size. Defaults to 10000.
    #       parse_watertypes (list, optional): Used to parse watertypes column into split columns. Defaults to False.
    def parse_data_dump(self,
                        api_key: str,
                        query_url: str,
                        query_filter: str = None,
                        skip_properties: str = None,
                        page: int = 1,
                        page_size: int = 1000000,
                        parse_watertypes=False):

        json_request_list = []

        while True:
            request_url = self.url_builder(
                query_url, query_filter, skip_properties, page, page_size)
            try:
                request = requests.get(
                    request_url, headers={"Accept": "application/json", "x-api-key": api_key}).json()
                response = request['result']
                json_request_list.extend(response)

                if self.check_ending(request, page_size):
                    return self.return_dataframe(json_request_list, parse_watertypes)

                page += 1

            except requests.HTTPError as e:
                if self.http_error_check(e):
                    print(e)
                    break

    # Returns dataframe and parses watertypes column if it is in the set.
    # Args: data (list_:JSON object from aquadesk API
    # Returns: pd.DataFrame: returns dataframe of query
    def return_dataframe(self,
                         json_object: list,
                         parse_watertypes: bool) -> pd.DataFrame:
        df=pd.json_normalize(json_object)
        if ("watertypes" in df.columns) & (parse_watertypes == True):
            watertypes_nan_dict = {'classificationsystem': np.nan, 'watertypecode': np.nan}
            return pd.concat([df.drop("watertypes", axis=1),
                              pd.json_normalize(df["watertypes"].apply(lambda x: x[0] if isinstance(x, list) else watertypes_nan_dict))], axis=1)
        else:
            return df