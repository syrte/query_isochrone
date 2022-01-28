# query_isochrone

A handy script for querying the new parsec website of padova isochrones.

Author: Zhaozhou Li (http://github.com/syrte)

## Features
  - Easy to use
  - Flexibility
  - Friendly error prompts
  - Support latest also previous versions of parsec website
  - Decompress .gz files on the fly
## Dependencies
  - `requests`
  - `lxml`
## Usage
```
# initialize
cmd = ParsecQuery()

# query single isochrone
tab1 = cmd.query_isochrones(t=1e9, Z=0.0152)

# query multiple isochrones
tab2 = cmd.query_isochrones(t=np.linspace(1e9, 3e9, 3), Z=0.0152)

# or
cmd.query_isochrones(t=np.linspace(1e9, 3e9, 3), Z=[0.01, 0.02, 0.03])

# query simulated cluster and save
tab3 = cmd.query(isoc_agelow=1e9, isoc_metlow=0, sim_mtot=1e3, isoc_ismetlog=1, output_kind=3)
tab3.write('mock_data.fits')

# error message with invalid input
tab4 = cmd.query_isochrones(t=1e15, Z=0.0152)

# show options
cmd.show_options()

# check comments of the table, it should end with 'isochrone terminated'
tab1.meta['comments']

# use earlier cmd version
cmd28 = ParsecQuery(version='cmd_2.8')
cmd28.show_options()
cmd28.query_isochrones(t=1e10, Z=0.02)
cmd28.query_isochrones(lgt=8, Z=np.linspace(0.01, 0.02, 3))
cmd28.query_isochrones(t=np.logspace(6, 8, 3), Z=0.02)
```
