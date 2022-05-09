import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from .ddecoapidataparser import dataparser
from .config import apiKey

#---------------------------------------------
# File: data_validation.py
# Author: Wouter Abels (wouter.abels@rws.nl)
# Created: 10/01/22
# Last modified: 07/02/2022
# Python ver: 3.9.7
#---------------------------------------------

### Class for Datavalidation ###
class DataValidation:


    # Load data form api and merge dataframes     
    def data_load(self):

        # Call api key values
        api_key = apiKey
        # configure api url
        ddecoapi = dataparser('https://ddecoapi.aquadesk.nl/v2/')

        # Get filtered dataframe of requested data
        # To Do - Add Skip properties
        # Link for Filters: https://github.com/DigitaleDeltaOrg/dd-eco-api/blob/main/filtering.md
        data = ddecoapi.parse_data_dump(query_url = 'measurements', query_filter = 'measurementdate:ge:"2021-04-01";taxontype:eq:"MACEV"', api_key = api_key, skip_properties='calculatedunit,changedate,compartment,measuredunit,measurementpackage,measurementpurpose,measurementattributes,organisation,parametertype,projects,analysiscontext,samplingcontext,quantity,taxontype,externalkey,sourcesystem,supplier,organisationnumericcode,suppliernumericcode,watertypes,locationgeography.coordinates,locationgeography.type,locationgeography.srid,measurementgeography.coordinates,measurementgeography.type,measurementgeography.srid')
        measurement_data = ddecoapi.parse_data_dump(query_url= 'measurements', query_filter = 'measurementdate:ge:"2021-04-01";measurementpackage:eq:"ME.KG"', api_key = api_key, skip_properties='limitsymbol,measurementpurpose,organisation,projects,analysiscontext,samplingcontext,measurementsetnumber,externalkey,sourcesystem,supplier,organisationnumericcode,suppliernumericcode,watertypes,locationgeography.coordinates,locationgeography.type,locationgeography.srid,measurementgeography.coordinates,measurementgeography.type,measurementgeography.srid,parameter,parametertype,classifiedvalue')

        data_measurementobjects = pd.unique(data['measurementobject'])
        data_historic = []
        for object in data_measurementobjects:
            filter = 'taxontype:eq:"MACEV";measurementdate:ge:"2015-01-01";measurementobject:eq:' + "'" + object + "'"
            data_measurementobject = ddecoapi.parse_data_dump(query_url= 'measurements', query_filter= filter  , api_key = api_key,skip_properties='calculatedunit,changedate,compartment,measuredunit,,measurementpackage,measurementpurpose,measurementattributes,organisation,parametertype,projects,analysiscontext,samplingcontext,quantity,taxontype,measurementsetnumber,externalkey,sourcesystem,supplier,organisationnumericcode,suppliernumericcode,watertypes,locationgeography.coordinates,locationgeography.type,locationgeography.srid,measurementgeography.coordinates,measurementgeography.type,measurementgeography.srid')
            data_historic = data_measurementobject.append(data_historic)

        # Load twn data and taxongroup names
        twn = ddecoapi.parse_data_dump(query_url = 'parameters', query_filter = 'parametertype:eq:"TAXON";taxontype:eq:"MACEV"', api_key = api_key, skip_properties='code,changedate,externalkey,parametertype,taxonmaintype,taxontype,authors,parentauthors,literature,standards,synonymauthors')
        taxongroups = ddecoapi.parse_data_dump(query_url = 'taxongroups', api_key = api_key, skip_properties='maintypename,changedate,externalkey')

        # Merge twn data and taxongroup names
        twn = twn.merge(taxongroups, how = 'left', left_on = 'taxongroup', right_on = 'code', suffixes = (None, '_tg'))

        # Return Loaded data to function
        return data, data_historic, twn, taxongroups, measurement_data

    
    # Check and modify data before validation
    def data_check(self):
    
        # Load data from data_load_test function
        data, data_historic, twn, taxongroups, measurement_data = DataValidation().data_load()

        # Add historic data to current data for complete data set
        historic_and_data = data_historic.append(data)

        # Check for limitsymbol if True then replace 0 measured value to 1
        data['measuredvalue'] = np.where(((data.limitsymbol == '>') & (data.measuredvalue == 0.0)), 1, data.measuredvalue)
        historic_and_data['measuredvalue'] = np.where(((historic_and_data.limitsymbol == '>') & (historic_and_data.measuredvalue == 0.0)), 1, historic_and_data.measuredvalue)

        # Makesure the values in the externalreference(collectienummer) and id column are string type values
        data['externalreference'] = data['externalreference'].astype(str)
        data['id'] = data['id'].astype(str)
        historic_and_data['externalreference'] = historic_and_data['externalreference'].astype(str)
        historic_and_data['id'] = historic_and_data['id'].astype(str)

        # Merge data and twn
        data = data.merge(twn, how='left', left_on='parameter', right_on='name', suffixes = (None, '_twn'))
        historic_and_data = historic_and_data.merge(twn, how='left', left_on='parameter', right_on='name', suffixes = (None, '_twn'))

        # Add group for rows where taxongroup is empty
        data['taxongroup'] = data['taxongroup'].astype(str)
        data['taxongroup'] = np.where((data.taxongroup == 'nan'), 'no_group', data.taxongroup)
        data_historic['taxongroup'] = data_historic['taxongroup'].astype(str)
        data_historic['taxongroup'] = np.where((data_historic.taxongroup == 'nan'), 'no_group', data_historic.taxongroup)

        # Check statuscode if 20 replace name with parentname
        data['parameter'] = np.where((data.statuscode == 20), data.synonymname, data.parameter)
        historic_and_data['parameter'] = np.where((historic_and_data.statuscode == 20), historic_and_data.synonymname, historic_and_data.parameter)

        # Check for genus and add a column with higher genus information
        data['genus'] = data['parameter']
        data['genus'] = np.where((data.taxonrank == 'Species'), data.parentname, data.genus)
        data['genus'] = np.where((data.taxonrank == 'SpeciesCombi'), data.parentname, data.genus)
        historic_and_data['genus'] = historic_and_data['parameter']
        historic_and_data['genus'] = np.where((historic_and_data.taxonrank == 'Species'), historic_and_data.parentname, historic_and_data.genus)
        historic_and_data['genus'] = np.where((historic_and_data.taxonrank == 'SpeciesCombi'), historic_and_data.parentname, historic_and_data.genus)

        # Return checked data
        return  data, historic_and_data, data_historic, twn, taxongroups, measurement_data

    ###Statistics and Data Analysis###
    # Set colours per taxongroup
    def set_data_colours(self):
        macev_taxongroup_colours = {
            'Annelida/Platyhelminthes - Hirudinea':'aqua', \
            'Annelida/Platyhelminthes - Polychaeta':'skyblue', \
            'Annelida/Platyhelminthes - Oligochaeta':'dodgerblue', \
            'Annelida/Platyhelminthes - Turbellaria':'darkblue', \
            'Arachnida':'dimgray', \
            'Bryozoa - Hydrozoa - Porifera':'lightgrey', \
            'Crustacea - Amphipoda':'pink', \
            'Crustacea - Decapoda':'magenta', \
            'Crustacea - Isopoda':'violet', \
            'Crustacea - Mysida':'purple', \
            'Crustacea - Remaining':'blueviolet', \
            'Echinodermata':'ivory', \
            'Insecta (Diptera) - Chironomidae':'orange', \
            'Insecta (Diptera) - Remaining':'limegreen', \
            'Insecta (Diptera) - Simuliidae':'green', \
            'Insecta - Coleoptera':'lawngreen', \
            'Insecta - Ephemeroptera':'seagreen', \
            'Insecta - Heteroptera':'darkolivegreen', \
            'Insecta - Lepidoptera':'mediumspringgreen', \
            'Insecta - Odonata':'greenyellow', \
            'Insecta - Remaining':'palegreen', \
            'Insecta - Trichoptera':'yellowgreen', \
            'Marien - Remaining':'dimgrey', \
            'Mollusca - Bivalvia':'yellow', \
            'Mollusca - Gastropoda':'gold', \
            'Collembola':'black' 
            }
        return macev_taxongroup_colours

    # Divide dataset per year and calculate relative distribution per year, return te values from series to a dataframe and reset the first column to index and add column titles remove empty columns with only 0 values
    def value_per_year(self, relative_data_location_year):
        years = ['2000','2001','2002','2003','2004','2005','2006','2007','2008','2009','2010','2011','2012','2013','2014','2015','2016','2017','2018','2019','2020','2021','2022']
        dataperyear = {}
        for year in years:
            dataperyear[year] = relative_data_location_year[relative_data_location_year['collectiondate']\
                .str\
                .contains(year)]\
                .groupby('name_tg')['calculatedvalue']\
                .sum()\
                .astype(int)\
                .to_frame()\
                .rename_axis('Taxongroup')\
                .rename(columns={'calculatedvalue':year})
        dataperyear = pd.concat(dataperyear, join='outer', axis=1)\
            .fillna(0)\
            .astype(int)
        dataperyear = dataperyear.loc[:, (dataperyear!=0)\
            .any(axis=0)]
        dataperyear.columns = dataperyear.columns.droplevel()
        dataperyear = dataperyear.T
        return dataperyear

    # Divide data per location
    def data_location(self, historic_and_data, object):
        datalocation = historic_and_data[historic_and_data["measurementobjectname"].str.contains(object)]
        return datalocation

    # Calls 2 functions and calculates the relative values of de resulting dataframe 
    def relative_data_location_per_year(self, object, historic_and_data):
        relative_data_location_year = DataValidation().data_location(object, historic_and_data) 
        relative_data_location_year = DataValidation().value_per_year(relative_data_location_year)
        relative_data_location_year = relative_data_location_year
        return relative_data_location_year

    # Plot relative counts per taxon groups
    def plot_total_abundance(self):
        data, historic_and_data, data_historic, twn, taxongroups, measurement_data = DataValidation().data_check()
        macev_taxongroup_colours = DataValidation().set_data_colours()
        total_plot_data = DataValidation().value_per_year(historic_and_data)#.apply(lambda x: x*100/sum(x),axis=1)
        return total_plot_data, macev_taxongroup_colours
    
    def plotly_data(self):
        data, historic_and_data, data_historic, twn, taxongroups, measurement_data = DataValidation().data_check()
        macev_taxongroup_colours = DataValidation().set_data_colours()
        total_plot_data = DataValidation().value_per_year(historic_and_data)
        unique_measurementobject = np.sort(pd.unique(historic_and_data['measurementobjectname']))
        return total_plot_data, macev_taxongroup_colours, unique_measurementobject, historic_and_data