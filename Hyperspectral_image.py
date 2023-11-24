import spectral.io.envi as envi
from getpass import getuser
import numpy as np
from variables import wavelengths
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
import platform

def normalize(im):
    min, max = im.min(), im.max()
    return (im.astype(float)-min)/(max-min)

def extract_filename(filepath):
    filename = filepath.split("/")[-1]
    if len(filename) > 17:
        filename = "..." + filename[-7:]
    return filename

def wavelength_to_rgb(wavelength):
    gamma = 0.8
    intensity_max = 255
    factor = 0.0
    R, G, B = (0,0,0)
    
    if (wavelength < 380) or (wavelength > 750):
        return (0.5, 0.5, 0.5)

    if (wavelength >= 380) and (wavelength < 440):
        R = -(wavelength - 440) / (440 - 380)
        G = 0.0
        B = 1.0
    elif (wavelength >= 440) and (wavelength < 490):
        R = 0.0
        G = (wavelength - 440) / (490 - 440)
        B = 1.0
    elif (wavelength >= 490) and (wavelength < 510):
        R = 0.0
        G = 1.0
        B = -(wavelength - 510) / (510 - 490)
    elif (wavelength >= 510) and (wavelength < 580):
        R = (wavelength - 510) / (580 - 510)
        G = 1.0
        B = 0.0
    elif (wavelength >= 580) and (wavelength < 645):
        R = 1.0
        G = -(wavelength - 645) / (645 - 580)
        B = 0.0
    elif (wavelength >= 645) and (wavelength <= 750):
        R = 1.0
        G = 0.0
        B = 0.0
        
    if (wavelength >= 380) and (wavelength < 420):
        factor = 0.3 + 0.7*(wavelength - 380) / (420 - 380)
    elif (wavelength >= 420) and (wavelength < 645):
        factor = 1.0
    elif (wavelength >= 645) and (wavelength <= 750):
        factor = 0.3 + 0.7*(750 - wavelength) / (750 - 645)
        
    R = round(intensity_max * (R * factor)**gamma)
    G = round(intensity_max * (G * factor)**gamma)
    B = round(intensity_max * (B * factor)**gamma)
    
    return (R/255.0, G/255.0, B/255.0)

class SpectralImage():
    def __init__(self: None, bilPath: str, hdrPath: str) -> None:
        self.bil = bilPath
        self.hdr = hdrPath
        leaf_ref = envi.open(self.hdr, self.bil)
        dats = np.asarray(leaf_ref.load())
        self.values = np.flipud(dats)
        self._bgr_calculated = None  # Inicializado en None

    def BGR(self):
        # Si ya se ha calculado previamente, simplemente retornar el valor
        if self._bgr_calculated is not None:
            return self._bgr_calculated

        aux_r = self.values[0][:, 150:151]
        aux_g = self.values[0][:, 80:81]
        aux_b = self.values[0][:, 36:37]
        for i in range(1, self.values.shape[0]):
            aux_r = np.concatenate((aux_r, self.values[i][:, 150:151]), axis=1)
            aux_g = np.concatenate((aux_g, self.values[i][:, 80:81]), axis=1)
            aux_b = np.concatenate((aux_b, self.values[i][:, 36:37]), axis=1)
        R = normalize(aux_r)
        G = normalize(aux_g)
        B = normalize(aux_b)
        self._bgr_calculated = np.dstack((R, G, B))
        
        return self._bgr_calculated

    def applyMask(self):pass
    def reduceChannels(self):pass #Idea: usar PCA, ICA o Autoencoders para reducir los canales y visualizar el resultado.


if __name__ == "__main__":pass