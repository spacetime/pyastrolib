#!/usr/bin/env python
# This file is part of pyAstroLib.
#
# pyAstroLib is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyAstroLib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser Public License
# along with pyAstroLib.  If not, see <http://www.gnu.org/licenses/>.

import numpy as n

def adstring(ra_dec, dec="", precision="", truncate=""):
  

  # Testing Input Parameters

  if n.size(ra_dec) == 1:
    if not dec:
      dec = ra_dec
    else:
      ra = ra_dec
  elif n.size(ra_dec) == 2:
    if n.size(dec) < 2:
      ra = n.mod(ra_dec[0], 360)
      if (not precision):
        precision = dec
      dec = ra_dec[1]
  else: ra = ra_dec
  
  if n.size(ra) != n.size(dec):
    raise TypeError, 'ERROR - RA and Declination do not have equal number of elements'

  if n.size(ra) == n.size(dec):
      badrange = n.where( (dec > 90 ) or (dec < -90)  )
      if n.size(badrange) > 0:
        print "Warning:  Some declination values are out of valid range (-90 < dec <90)"
                    



  return 0

def ccm_unred(wave, flux, ebv, r_v=""):
    """ccm_unred(wave, flux, ebv, r_v="")
    Deredden a flux vector using the CCM 1989 parameterization 
    Returns an array of the unreddened flux
  
    INPUTS:
    wave - array of wavelengths (in Angstroms)
    dec - calibrated flux array, same number of elements as wave
    ebv - colour excess E(B-V) float. If a negative ebv is supplied
          fluxes will be reddened rather than dereddened     
  
    OPTIONAL INPUT:
    r_v - float specifying the ratio of total selective
          extinction R(V) = A(V)/E(B-V). If not specified,
          then r_v = 3.1
            
    OUTPUTS:
    funred - unreddened calibrated flux array, same number of 
             elements as wave
             
    NOTES:
    1. This function was converted from the IDL Astrolib procedure
       last updated in April 1998. All notes from that function
       (provided below) are relevant to this function 
       
    2. (From IDL:) The CCM curve shows good agreement with the Savage & Mathis (1979)
       ultraviolet curve shortward of 1400 A, but is probably
       preferable between 1200 and 1400 A.

    3. (From IDL:) Many sightlines with peculiar ultraviolet interstellar extinction 
       can be represented with a CCM curve, if the proper value of 
       R(V) is supplied.

    4. (From IDL:) Curve is extrapolated between 912 and 1000 A as suggested by
       Longo et al. (1989, ApJ, 339,474)

    5. (From IDL:) Use the 4 parameter calling sequence if you wish to save the 
       original flux vector.

    6. (From IDL:) Valencic et al. (2004, ApJ, 616, 912) revise the ultraviolet CCM
       curve (3.3 -- 8.0 um-1).    But since their revised curve does
       not connect smoothly with longer and shorter wavelengths, it is
       not included here.
 
    7. For the optical/NIR transformation, the coefficients from 
       O'Donnell (1994) are used
  
    >>> ccm_unred([1000, 2000, 3000], [1, 1, 1], 2 ) 
    array([9.7976e+012, 1.12064e+07, 32287.1])
    """
    wave = n.array(wave, float)
    flux = n.array(flux, float)
    
    if wave.size != flux.size: raise TypeError, 'ERROR - wave and flux vectors must be the same size'
    
    if not bool(r_v): r_v = 3.1 

    x = 10000.0/wave
    npts = wave.size
    a = n.zeros(npts, float)
    b = n.zeros(npts, float)
    
    ###############################
    #Infrared
    
    good = n.where( (x > 0.3) & (x < 1.1) )
    a[good] = 0.574 * x[good]**(1.61)
    b[good] = -0.527 * x[good]**(1.61)
    
    ###############################
    # Optical & Near IR

    good = n.where( (x  >= 1.1) & (x < 3.3) )
    y = x[good] - 1.82
    
    c1 = n.array([ 1.0 , 0.104,   -0.609,    0.701,  1.137, \
                  -1.718,   -0.827,    1.647, -0.505 ])
    c2 = n.array([ 0.0,  1.952,    2.908,   -3.989, -7.985, \
                  11.102,    5.491,  -10.805,  3.347 ] )

    a[good] = n.polyval(c1[::-1], y)
    b[good] = n.polyval(c2[::-1], y)

    ###############################
    # Mid-UV
    
    good = n.where( (x >= 3.3) & (x < 8) )   
    y = x[good]
    F_a = n.zeros(n.size(good),float)
    F_b = n.zeros(n.size(good),float)
    good1 = n.where( y > 5.9 )    
    
    if n.size(good1) > 0:
        y1 = y[good1] - 5.9
        F_a[ good1] = -0.04473 * y1**2 - 0.009779 * y1**3
        F_b[ good1] =   0.2130 * y1**2  +  0.1207 * y1**3

    a[good] =  1.752 - 0.316*y - (0.104 / ( (y-4.67)**2 + 0.341 )) + F_a
    b[good] = -3.090 + 1.825*y + (1.206 / ( (y-4.62)**2 + 0.263 )) + F_b
    
    ###############################
    # Far-UV
    
    good = n.where( (x >= 8) & (x <= 11) )   
    y = x[good] - 8.0
    c1 = [ -1.073, -0.628,  0.137, -0.070 ]
    c2 = [ 13.670,  4.257, -0.420,  0.374 ]
    a[good] = n.polyval(c1[::-1], y)
    b[good] = n.polyval(c2[::-1], y)

    # Applying Extinction Correction
    
    a_v = r_v * ebv
    a_lambda = a_v * (a + b/r_v)
    
    funred = flux * 10.0**(0.4*a_lambda)   

    return funred

def radec(ra, dec, hours=""):
  """radec(ra, dec, hours="")
  Converts RA and Dec from decimal to sexigesimal units
  Returns a tuple (ihr, imin, xsec, imn, wsc)
  
  INPUTS:
    ra - right ascension, float or array, in degrees unless 
         "hours" is set
    dec - declination in decimal degrees, float or array, same
          number of elements as ra     
  
  OPTIONAL INPUT:
    hours - if set to true, then the right ascension input should
            be set to hours instead of degrees
            
  OUTPUTS:
    ihr - right ascension hours (float or array)
    imin - right ascension minutes (float or array)
    xsec - right ascension seconds (float or array)
    ideg - declination degrees (float or array)
    imn - declination minutes (float or array)
    xsc - declination seconds (float or array)         
  
  >>> radec(0,0) 
  array(0,0,0,0,0)
  """


  # Compute RA
  if(hours):
    ra =  n.mod(ra, 24)
    ra = ra + 24*(n.less(ra, 0) )
    ihr = n.fix(ra)
    xmin = n.abs(ra*60.0 - ihr*60.0)
  else:
    ra = n.mod(ra, 360)
    ra = ra + 360*(n.less(ra, 0))
    ihr = n.fix(ra/15.0)
    xmin = n.abs(ra*4.0 - ihr*60.0)

  imin = n.fix(xmin)
  xsec = (xmin - imin)*60.0

  # Compute Dec
  ideg = n.fix(dec)
  xmn = n.abs(dec - ideg)*60.0
  imn = n.fix(xmn)
  xsc = (xmn - imn)*60.0

  # Testing for Special Case of Zero Degrees

  zero_deg = n.equal(ideg, 0)  & n.less(dec, 0) 
  imn = imn - 2*imn*n.fix( zero_deg * ( n.not_equal(imn,0) ) )
  xsc = xsc - 2 *xsc*zero_deg*(n.equal(imn, 0) )  

  return ihr, imin, xsec, ideg, imn, xsc

def sixty(scalar):
    """ sixty(scalar)
    Converts a decimal number to sexigesimal
    returns a three element array
    
    INPUTS: 
      scalar - Decimal Quantity
      
    OUTPUTS: 
      result - three element array of sexigesimal equivalent.
               If the scalar is negative, the first non-zero
               element in the result will have a negative sign
               
    COMPATIBILITY NOTES:
      1. Since python does not support negative zeros, the trail
         sign keyword from the IDL procedure has been removed
    
    >>>sixty(53)
    [53.0, 0.0, 0.0]
    """
    if n.size(scalar) != 1:
            raise TypeError, 'ERROR - Parameter must contain 1 element'
    
    ss = n.abs(3600.0 * scalar)
    mm = n.abs(60.0 * scalar)
    dd = n.abs(scalar)
    result = n.zeros(3, float)  
    
    result[0] = n.fix(dd)
    result[1] = n.fix(mm - 60.0*result[0] )
    result[2] = ss - 3600.0*result[0] - 60.0*result[1]
    
    if scalar < 0.0:
        if result[0] != 0:
            result[0] = -result[0]
        elif result[1] != 0:
            result[1] = -result[1]
        else: 
            result[2] = -result[2]
    
    return result

def ten(dd, mm="", ss=""):
    """ ten(dd, mm="", ss="")
    Converts a sexigesimal number to decimal 
    returns a float
    
    INPUTS: 
      dd - Either a scalar representing the hours or degrees
           or a 3 element array representing all three sexigesimal
           quantities
      mm - A scalar representing the minutes (optional)
      ss - A scalar representing the seconds (optional)   
      
    OUTPUTS: 
      result - A scalar representing the decimal quantity
               If any of the input elements are negative, the 
               result will have a negative sign
               
    >>>ten(2, 60, 3600)
    4.0
    """
    
    if (not bool(mm) and (not bool(ss)) ):
        vector = n.array(dd)
    else:
        vector = n.zeros(3, float)
        vector[0] = dd
        vector[1] = mm
        if (bool(ss)): vector[2] = ss
      
    ndim = n.ndim(vector)
    nel = n.size(vector)

    if nel > 3: raise TypeError, 'ERROR - There can be no more than 3 elements in the input'

    if ndim == 0: return vector
    
    facs = [1.0, 60.0, 3600.0]
    
    negsign = bool(n.sum(n.where(vector < 0)))
    
    vector = n.abs(vector)
    decim = 0.0
    
    for i in range(nel):
        decim = decim + vector[i]/facs[i] 
    
    if negsign: decim = decim * -1.0
       
    return decim

if __name__ == '__main__':
  # The following two lines will test all functions in the module.
  # Run `python astro.py -v` to see verbose output.  It's probably best to rely
  # on this kind of testing once you believe the code to already be functional
  # since it is a great method for building but difficult to work with durring
  # development.
  import doctest
  doctest.testmod()
