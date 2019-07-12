# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.4'
#       jupytext_version: 1.1.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # International Passenger Survey 4.01, citizenship group by sex by age by country of last or next residence
#
# Convert all tabs from latest Excel spreadsheet available from https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/internationalmigration/datasets/ipscitizenshipgroupbysexbyagebycountryoflastornextresidence

# +
from gssutils import *

scraper = Scraper('https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/' \
                  'internationalmigration/datasets/ipscitizenshipgroupbysexbyagebycountryoflastornextresidence')
scraper
# -

tabs = scraper.distribution().as_databaker()

# Each tab is of the same form, with "software readable codes":
#
# > The datasheets can be imported directly into suitable software. When importing the datasheets into other software import only rows 8 to 1448, starting at column F.

# +
tidied_sheets = []

for tab in tabs:
    if not tab.name.startswith('Data'):
        continue
    year = int(tab.excel_ref('A2').value[-4:])
    start = tab.excel_ref('F8')
    end = tab.excel_ref('F1448')
    #end = tab.excel_ref('F48')
    codes = start.fill(DOWN) & end.expand(UP)
    observations = codes.fill(RIGHT).is_not_whitespace()
    country = start.shift(RIGHT).fill(RIGHT)
    country_ci = country.regex(r'^.*CI\s*$')
    country_est = country - country_ci
    observations_est = observations & country_est.fill(DOWN)
    observations_ci = observations & country_ci.fill(DOWN)
    cs_est = ConversionSegment(observations_est, [
        HDimConst('Year', year),
        HDim(codes, 'Code', DIRECTLY, LEFT),
        HDim(country_est, 'Country of Residence', DIRECTLY, ABOVE),
        HDim(observations_ci, 'CI', DIRECTLY, RIGHT),
        HDimConst('Measure Type', 'Count'),
        HDimConst('Unit', 'people-thousands')
    ])
    #savepreviewhtml(cs_est)
    tidy_sheet = cs_est.topandas()
    tidy_sheet.rename(columns={'OBS': 'Value', 'DATAMARKER': 'IPS Marker'}, inplace=True)
    tidied_sheets.append(tidy_sheet)
    break
tidy = pd.concat(tidied_sheets)
tidy


# +
def residence_country_code(s):
    code = pathify(s)
    assert code.startswith('resc-'), code
    code = code[5:]
    assert code.endswith('-est'), code
    code = code[:-4]
    return code.replace('-/-', '-')

tidy['Country of Residence'] = tidy['Country of Residence'].apply(residence_country_code)
codes_table = tidy['Code'].str.split(', ', expand=True)
tidy['Migration Flow'] = codes_table[0]
tidy['IPS Citizenship'] = codes_table[1]
tidy['Sex'] = codes_table[2]
tidy['Age'] = codes_table[3]
tidy = tidy[['Year','Country of Residence','Migration Flow',
             'IPS Citizenship','Sex','Age',
             'Measure Type','Value','IPS Marker','CI','Unit']]
tidy
# -

from IPython.core.display import HTML
for col in tidy:
    if col not in ['Value', 'CI']:
        tidy[col] = tidy[col].astype('category')
        display(HTML(f"<h2>{col}</h2>"))
        display(tidy[col].cat.categories)

tidy['Country of Residence'] = tidy['Country of Residence'].cat.rename_categories({
    'bahamas-the': 'bahamas'
})
tidy['Migration Flow'].cat.categories = tidy['Migration Flow'].cat.categories.map(pathify)
tidy['IPS Citizenship'].cat.categories = tidy['IPS Citizenship'].cat.categories.map(lambda s: pathify(s[4:]))
tidy['Sex'] = tidy['Sex'].cat.rename_categories({
    'Female': 'F',
    'Male': 'M',
    'Persons': 'T'})
tidy['Age'].cat.categories = tidy['Age'].cat.categories.map(
    lambda s: 'all' if s == 'Age All' else pathify(s[:3]) + '/' + pathify(s[4:]))
tidy['IPS Marker'].cat.rename_categories({
    'z': 'not-applicable',
    '.': 'no-contact',
    '0~': 'rounds-to-zero'})
tidy

out = Path('out')
out.mkdir(exist_ok=True)
tidy.to_csv(out / 'observations.csv', index = False)

# +
from gssutils.metadata import THEME

scraper.dataset.family = 'migration'
scraper.dataset.theme = THEME['population']
with open(out / 'dataset.trig', 'wb') as metadata:
    metadata.write(scraper.generate_trig())
# -
csvw = CSVWMetadata('https://ons-opendata.github.io/ref_migration/')
csvw.create(out / 'observations.csv', out / 'observations.csv-schema.json')


# Alternate output using CSVW directly

tidy['Measure Type'].cat.categories = tidy['Measure Type'].cat.categories.map(pathify)
tidy.to_csv(out / 'observations-alt.csv', index = False)
csvw.create(out / 'observations-alt.csv', out / 'observations-alt.csv-metadata.json', with_transform=True,
            base_url='http://gss-data.org.uk/data/', base_path='gss_data/migration/ons-ltim-passenger-survey-4-01',
            dataset_metadata=scraper.dataset.as_quads())


