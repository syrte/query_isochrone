"""
A handy script for querying the new CMD website of Padova/PARSEC isochrones.

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
"""

import numpy as np
import requests
from lxml import etree
from urllib.parse import urljoin
from collections import defaultdict
from astropy.io import ascii
import gzip
import json

__author__ = "lizz.astro@gmail.com"
__version__ = "1.1"

__all__ = ["ParsecQuery"]


def parse_form(form):
    """
    Parse the form data from a string to a dictionary.

    Parameters
    ----------
    form : str
        The form data should be strings separated by colon in each line

    Returns
    -------
    dict
        The parsed form data as a dictionary.
    """
    return dict(
        [
            [i.strip() for i in item.split(":")]
            for item in form.strip("\n").split("\n")
        ]
    )


def isscalar(x):
    """
    Check if the input is scalar.

    Parameters
    ----------
    x : any
        The input to check.

    Returns
    -------
    bool
        True if the input is scalar, False otherwise.
    """
    if x is None:
        return True
    else:
        return np.isscalar(x)


class ParsecQuery:
    def __init__(
        self,
        version="cmd",
        website="https://stev.oapd.inaf.it/cgi-bin/",
    ):
        """
        Initialize the ParsecQuery class.

        Parameters
        ----------
        version : str, optional
            The cmd version, "cmd" for the default version. Can set version explicitly,
            e.g., "cmd_3.7", "cmd_3.8".
        website : str, optional
            The cmd website URL.
        """
        self.website = urljoin(website + "/", version)

        self._get_args()
        self.args_default = self.args_default_website

        if version == "cmd" or version >= "cmd_3":
            self.query_isochrones = self._query_isochrones_cmd3
        elif version >= "cmd_2":
            self.query_isochrones = self._query_isochrones_cmd2
        else:
            raise ValueError("Unknown cmd version!")

    def query(self, ret_table=True, **args):
        """
        Query the Parsec website and return the results.

        Parameters
        ----------
        ret_table : bool, optional
            Whether to return the results as a table (default is True).
        **args : dict
            Additional arguments to pass to the query.

        Returns
        -------
        astropy.table.Table or str
            The query results as an Astropy Table if ret_table is True, otherwise as a string.
        """
        r = requests.post(self.website, data={**self.args_default, **args})
        p = etree.HTML(r.content)
        url_output = p.xpath("//a[contains(text(), 'output')]/@href")
        if url_output:
            url = urljoin(self.website, url_output[0])
            output = requests.get(url).content
            if url.endswith(".gz"):
                output = gzip.decompress(output).decode("utf8")
            else:
                output = output.decode("utf8")
        else:
            msg = "".join(p.xpath("//p[@class='errorwarning']//text()"))
            if msg:
                raise ValueError(
                    f"Query failed. Error message:\n{msg}\nPlease check your inputs!"
                )
            else:
                msg = "\n".join(p.xpath("//form//text()"))
                if msg:
                    raise ValueError(
                        f"Query failed. Webpage returned:\n{msg}\n"
                    )
                else:
                    raise ValueError(
                        "Query failed. No useful information provided."
                    )

        if ret_table:
            for i, line in enumerate(output.splitlines()):
                if line.startswith("#"):
                    header = line[1:]
                else:
                    break
            names = header.split()
            if names[0] == "Z":
                names[0] = "Zini"
            table = ascii.read(output, names=names)
            return table
        else:
            return output

    def _query_isochrones_cmd3(
        self,
        t=None,
        lgt=None,
        Z=None,
        MeH=None,
        extinction_av=0,
        ret_table=True,
        **args,
    ):
        """
        Query isochrones with ages and metallicity for cmd version 3.
        Up to a maximum of 1e4 isochrones for single query.

        Parameters
        ----------
        t, lgt : float or array
            Age in years. If an array is given, it must be equally spaced.
        Z : float or array
            Metallicity. If an array is given, it must be equally spaced.
        MeH : float or array
            Metallicity [M/H], where [M/H]=log(Z/X)-log(Z/X)_sun, with (Z/X)_sun=0.0207
            and Y=0.2485+1.78Z for PARSEC tracks. If an array is given, 
            it must be equally spaced.
        extinction_av : float, optional
            Total extinction in magnitudes (default is 0).
        ret_table : bool, optional
            Whether to return the results as a table (default is True).
        **args : dict
            Additional arguments to pass to the query. Check show_options() for available options.

        Returns
        -------
        astropy.table.Table or str
            The query results as an Astropy Table if ret_table is True, otherwise as a string.
        """
        if t is not None:
            if isscalar(t):
                args.update(isoc_isagelog=0, isoc_agelow=t, isoc_dage=0)
            else:
                args.update(
                    isoc_isagelog=0,
                    isoc_agelow=t[0],
                    isoc_ageupp=t[-1],
                    isoc_dage=np.diff(t).mean(),
                )
        elif lgt is not None:
            if isscalar(lgt):
                args.update(isoc_isagelog=1, isoc_lagelow=lgt, isoc_dlage=0)
            else:
                args.update(
                    isoc_isagelog=1,
                    isoc_lagelow=lgt[0],
                    isoc_lageupp=lgt[-1],
                    isoc_dlage=np.diff(lgt).mean(),
                )
        else:
            raise ValueError("Must provide one of 't' or 'lgt'!")

        if Z is not None:
            if isscalar(Z):
                args.update(isoc_ismetlog=0, isoc_zlow=Z, isoc_dz=0)
            else:
                args.update(
                    isoc_ismetlog=0,
                    isoc_zlow=Z[0],
                    isoc_zupp=Z[-1],
                    isoc_dz=np.diff(Z).mean(),
                )
        elif MeH is not None:
            if isscalar(MeH):
                args.update(isoc_ismetlog=1, isoc_metlow=MeH, isoc_dmet=0)
            else:
                args.update(
                    isoc_ismetlog=1,
                    isoc_metlow=MeH[0],
                    isoc_metupp=MeH[-1],
                    isoc_dmet=np.diff(MeH).mean(),
                )
        else:
            raise ValueError("Must provide one of 'Z' or 'MeH'!")

        args.update(extinction_av=extinction_av)
        return self.query(ret_table, **args)

    def _query_isochrones_cmd2(
        self,
        t=None,
        lgt=None,
        Z=None,
        MeH=None,
        extinction_av=0,
        ret_table=True,
        **args,
    ):
        """
        Query isochrones with ages and metallicity for cmd version 2.

        Parameters
        ----------
        t, lgt : float or array
            Age in years. Must be equally spaced in log-scale if an array is given.
        Z : float or array
            Metallicity. Must be equally spaced if an array is given.
        MeH : float or array
            Metallicity [M/H], using the approximation [M/H]=log(Z/Zsun), with Zsun=0.019
            for Marigo et al. (2008) and previous tracks, and Zsun=0.0152 for PARSEC
            Bressan et al. (2012) and later tracks. Must be equally spaced in 10**MeH
            if an array is given.
        extinction_av : float, optional
            Total extinction in magnitudes (default is 0).
        ret_table : bool, optional
            Whether to return the results as a table (default is True).
        **args : dict
            Additional arguments to pass to the query. Check show_options() for available options.

        Returns
        -------
        astropy.table.Table or str
            The query results as an Astropy Table if ret_table is True, otherwise as a string.
        """
        if t is None:
            if lgt is None:
                raise ValueError("Must provide one of 't' or 'lgt'!")
            elif isscalar(lgt):
                t = 10**lgt
                lgt = None
        elif not isscalar(t):
            lgt = np.log10(t)
            t = None

        if Z is None:
            if MeH is None:
                raise ValueError("Must provide one of 'Z' or 'MeH'!")
            else:
                isoc_kind = args.get(
                    "isoc_kind", self.args_default["isoc_kind"]
                )
                if isoc_kind.startswith("parsec"):
                    Zsun = 0.0152
                else:
                    Zsun = 0.019
                Z = Zsun * 10**MeH
        if not isscalar(lgt) and not isscalar(Z):
            raise ValueError("At most one array is allowed for 't' and 'Z'!")

        if t is not None:
            if isscalar(Z):
                args.update(isoc_val="0", isoc_age=t, isoc_zeta=Z)
            else:
                args.update(
                    isoc_val="2",
                    isoc_age0=t,
                    isoc_z0=Z[0],
                    isoc_z1=Z[-1],
                    isoc_dz=np.diff(Z).mean(),
                )
        else:
            args.update(
                isoc_val="1",
                isoc_zeta0=Z,
                isoc_lage0=lgt[0],
                isoc_lage1=lgt[-1],
                isoc_dlage=np.diff(lgt).mean(),
            )

        args.update(extinction_av=extinction_av)
        return self.query(ret_table, **args)

    def _get_args(self):
        """
        Get the default arguments from the Parsec website.
        """
        r = requests.get(self.website)
        p = etree.HTML(r.content)
        # print('types:', *set([b.attrib['type'] for b in p.xpath("//input")]))
        # types: checkbox text radio submit hidden

        args = defaultdict(list)
        opts = defaultdict(list)
        for b in p.xpath("//input|//select"):
            name = b.attrib["name"]
            if b.tag == "select":
                for c in b.getchildren():
                    if c.tag != "option":
                        continue
                    value = c.attrib["value"]
                    selected = c.attrib.get("selected", "")

                    if selected:
                        args[name] = value
                        opts[name].append(value + " [x]")
                    else:
                        opts[name].append(value)
            else:
                type = b.attrib["type"]
                value = b.attrib["value"]
                checked = b.attrib.get("checked", "")

                if type == "text":
                    args[name] = value
                    opts[name] = value
                elif type == "hidden":
                    args[name].append(value)
                elif type == "radio":
                    if checked:
                        args[name] = value
                        opts[name].append(value + " [x]")
                    else:
                        opts[name].append(value)
                elif type == "checkbox":
                    if checked:
                        args[name] = "1"
                        opts[name] = ["0", "1 [x]"]
                    else:
                        args[name] = "0"
                        opts[name] = ["0 [x]", "1"]
                elif type == "submit":
                    pass
                else:
                    raise ValueError(f"Unknown input type: {type}")

        args["submit_form"] = "Submit"

        self.args_default_website = dict(args)
        self.opts = dict(opts)

    def _set_args_form_data(self, form_data):
        """
        Debugging function. One can capture the form data sent from the browser
        to the website and use it to set the default query form. The form data
        should be strings separated by colon in each line, such as
            photsys_file: YBC_tab_mag_odfnew/tab_mag_CSST.dat
        """
        self.args_default = parse_form(form_data)

    def show_options(self):
        """
        Show the available options for the Parsec query.
        """
        if not hasattr(self, "opts"):
            self._get_args()
        print(json.dumps(self.opts, indent=3))
