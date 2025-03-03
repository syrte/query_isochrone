# query_isochrone

A handy script for querying the new CMD website of Padova/PARSEC isochrones.

Author: Zhaozhou Li (http://github.com/syrte)

This code was written as a part of
**Li, Shao, Li, et al.** 2020, ApJ, 901, 49,
[*Modeling Unresolved Binaries of Open Clusters in the Color-Magnitude Diagram. I. Method and Application of NGC 3532*](https://ui.adsabs.harvard.edu/abs/2020ApJ...901...49L/abstract).

If you used this code in your research, a link to the repo and a citation to the above paper will be appreciated.

## Features
- Easy to use
- Flexible
- Friendly error prompts
- Supports the latest and previous versions of the PARSEC website
- Decompresses .gz files on the fly

## Dependencies
- `requests`
- `lxml`
- `astropy`

## Usage
```python
# Initialize
import parsec
cmd = parsec.ParsecQuery()

# Query a single isochrone, return an astropy Table
tab1 = cmd.query_isochrones(t=1e9, Z=0.0152)

# Query multiple isochrones
tab2 = cmd.query_isochrones(t=np.linspace(1e9, 3e9, 3), Z=0.0152)

# And with multiple metallicities
tab2 = cmd.query_isochrones(t=np.linspace(1e9, 3e9, 3), Z=[0.01, 0.02, 0.03])

# Query simulated cluster and save
tab3 = cmd.query(isoc_agelow=1e9, isoc_metlow=0, sim_mtot=1e3, isoc_ismetlog=1, output_kind=3)
tab3.write('mock_data.fits')

# Set the photometric system
cmd.query_isochrones(
    t=1e9, Z=0.0152,
    photsys_file="YBC_tab_mag_odfnew/tab_mag_CSST.dat")

# Error message with invalid input
tab4 = cmd.query_isochrones(t=1e15, Z=0.0152)
# returns
#  ValueError: Query failed. Error message:
#  Error: t=1e+15 is not valid. 
#  Please check your inputs!

# Show available options
cmd.show_options()

# Check comments of the table, it should end with 'isochrone terminated'
tab1.meta['comments']

# Use an earlier cmd version
cmd28 = ParsecQuery(version='cmd_2.8')
cmd28.show_options()
cmd28.query_isochrones(t=1e10, Z=0.02)
cmd28.query_isochrones(lgt=8, Z=np.linspace(0.01, 0.02, 3))
cmd28.query_isochrones(t=np.logspace(6, 8, 3), Z=0.02)
```

## FAQ
### How do I know what are the available options?
All the options on the website are customizable in the script as well. 
The following command will return the acceptable options on the website:
```python
cmd.show_options()
```
The meanings should be clear by their names. If not, please consult the website.
The options can be set when calling `query_isochrones`, e.g.,
```python
cmd.query_isochrones(
    t=1e9, Z=0.0152,
    photsys_file="YBC_tab_mag_odfnew/tab_mag_CSST.dat")
```
The options for age and metallicity should only be provided through the keyword arguments `t`, `lgt`, `Z`, `MeH`.

Example of the options for cmd_3.7. The default values are marked with `[x]`.
```
{
   "track_parsec": [
      "parsec_CAF09_v2.0",
      "parsec_CAF09_v1.2S [x]",
      "parsec_CAF09_v1.1",
      "parsec_CAF09_v1.0"
   ],
   "track_omegai": [
      "0.00 [x]",
      "0.30",
      "0.60",
      "0.80",
      "0.90",
      "0.95",
      "0.99"
   ],
   "track_colibri": [
      "parsec_CAF09_v1.2S_S_LMC_08_web [x]",
      "parsec_CAF09_v1.2S_S35",
      "parsec_CAF09_v1.2S_S07",
      "parsec_CAF09_v1.2S_NOV13",
      "no"
   ],
   "track_postagb": [
      "no [x]"
   ],
   "n_inTPC": "10",
   "eta_reimers": "0.2",
   "photsys_file": [
      "tab_mag_odfnew/tab_mag_.dat",
      "YBC_tab_mag_odfnew/tab_mag_2mass_spitzer.dat",
      "YBC_tab_mag_odfnew/tab_mag_2mass_spitzer_wise.dat",
      "YBC_tab_mag_odfnew/tab_mag_2mass.dat",
      "YBC_tab_mag_odfnew/tab_mag_ogle_2mass_spitzer.dat",
      "YBC_tab_mag_odfnew/tab_mag_ubvrijhk.dat [x]",
      ...
   ],
   "photsys_version": [
      "YBC",
      "YBCnewVega [x]",
      "odfnew"
   ],
   "dust_sourceM": [
      "nodustM",
      "sil",
      "AlOx",
      "dpmod60alox40 [x]",
      "dpmod"
   ],
   "dust_sourceC": [
      "nodustC",
      "gra",
      "AMC",
      "AMCSIC15 [x]"
   ],
   "extinction_av": "0.0",
   "extinction_coeff": [
      "constant [x]"
   ],
   "extinction_curve": [
      "cardelli [x]"
   ],
   "kind_LPV": [
      "1",
      "2",
      "3 [x]"
   ],
   "imf_file": [
      "tab_imf/imf_salpeter.dat",
      "tab_imf/imf_chabrier_exponential.dat",
      "tab_imf/imf_chabrier_lognormal.dat",
      "tab_imf/imf_chabrier_lognormal_salpeter.dat",
      "tab_imf/imf_kroupa_orig.dat [x]"
   ],
   ...
   "output_kind": [
      "0 [x]",
      "1",
      "3",
      "4"
   ],
   "lf_maginf": "-15",
   "lf_magsup": "20",
   "lf_deltamag": "0.5",
   "sim_mtot": "1.0e4",
   "output_gzip": [
      "0 [x]",
      "1"
   ]
}
```

## Future Plan
I might add support for other isochrone models in the future (if I start to use them...).