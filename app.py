# -*- coding: utf-8 -*-
from flask import Flask, Response, request, render_template
from wtforms import Form, IntegerField, StringField, validators, IntegerField, widgets, FieldList, FormField, ValidationError
from flask_wtf.csrf import CSRFProtect
from polyglot import PolyglotForm
import json
import os
import urllib.request

app = Flask(__name__)

csrf = CSRFProtect(app)
app.secret_key = '"\xf9$T\x88\xefT8[\xf1\xc4Y-r@\t\xec!5d\xf9\xcc\xa2\xaa'
#app.secret_key = '"gh567n7j'                 
G, P = "GET", "POST"
app.config.update(SESSION_COOKIE_SAMESITE="Lax")

ttb = "top-to-bottom"
btt = "bottom-to-top" #46

def validoi(form, field):
    #global m
    #global s2
    s2 = "Nimen pituuden minimi on kaksi kirjainta"
    m = 2    
    if len(field.data.strip()) < m:
        raise ValidationError(s2)
        
#========================================================        

@app.route('/', methods=[G, P])
def pelilauta():

    #laudan data
    with urllib.request.urlopen("https://europe-west1-ties4080.cloudfunctions.net/vt2_taso1") as response:
        l_data = json.load(response)

    ruutu_1 = l_data["first"]
    keno_suunta = l_data["balls"]
    leveys = 50
    korkeus = leveys 

    pelaaja1 = "Pelaaja 1"
    pelaaja2 = "Pelaaja 2"

    r_min = l_data["min"]
    r_max = l_data["max"]
    url_pu = "https://appro.mit.jyu.fi/ties4080/vt/vt2/red.svg"
    url_si = "https://appro.mit.jyu.fi/ties4080/vt/vt2/blue.svg"
    s1 = "Syöttömäsi arvo ei vastaa laudan koon minimin ja maksimin vaihteluväliä (" + str(r_min) + " - " + str(r_max) + ")"
    
    #luodaan lomake
    class PeliLauta(PolyglotForm):
        l_koko = IntegerField('Laudan koko',id="koko", default=r_min, widget = widgets.Input(input_type="number"), validators=[validators.NumberRange(min=r_min, max=r_max, message=s1)])
        pelaaja1 = StringField('Pelaaja 2', validators=[validators.InputRequired(), validoi])
        pelaaja2 = StringField('Pelaaja 2', validators=[validators.InputRequired(), validoi])

    if request.method == G and request.args:
        form = PeliLauta(request.args)
        form.validate()

    elif request.method == P:
        form = PeliLauta()
        form.validate()
        
    else:
        form = PeliLauta()
        
    #alustetaan ja pyydetään pelille parametrejä 
    poistettu, laheta, undo, viimeisin_poisto = None, None, None, None
   
    try:
        pelaaja1 = request.values.get("pelaaja1")
    except:
        pass

    try:
        pelaaja2 = request.values.get("pelaaja2")
    except:
        pass

    try:
        l_koko = int(request.values.get("l_koko"))
        if l_koko < r_min or l_koko > r_max:
            l_koko = r_min
    except:
        l_koko = r_min

    try:
        viimeisin_poisto = request.values.get("viimeisin_poisto")
    except:
        viimeisin_poisto = None

    try:
        laheta = request.values.get("laheta")
    except:
        laheta = None

    try:
        poistettu = request.values.get("poistettu")
    except:
        poistetu = None

    try:
        undo = request.values.get("undo")
    except:
        undo = None
    # generoidaan pelimerkit, kenosuunta määrittää lokaatiot jne.                                                                                                         
    if laheta:
        pmerkit = pelimerkki_gen(l_koko, keno_suunta)
    else:
        try:
            pmerkit = json.loads(request.values.get("pmerkit"))
            pmerkit = poista_merkki(pmerkit, poistettu)
        except:
            pmerkit = pelimerkki_gen(l_koko, keno_suunta)

    if undo:
        try:
            rivi_kumottava = int(viimeisin_poisto.split(":")[0])
            sarake_kumottava = int(viimeisin_poisto.split(":")[1])
            pmerkit = palauta_ed(pmerkit, rivi_kumottava, sarake_kumottava)
        except:
            pass
    #===================================================================
    return Response(render_template("pelilauta.xhtml", form=form, pelaaja1=pelaaja1, pelaaja2=pelaaja2, l_koko=l_koko, ruutu_1=ruutu_1, leveys=leveys, korkeus=korkeus, pmerkit=pmerkit, json_merkit=json.dumps(pmerkit, indent=None, separators=(',', ':')), url_pu=url_pu, url_si=url_si, poistettu=poistettu), mimetype="application/xhtml+xml;charset=UTF-8")
#sijoittaa pelimerkit "kenoiksi"
def pelimerkki_gen(l_koko, kenosuunta):
    pmerkit = {}
    if kenosuunta == ttb:
        for i in range(1, l_koko+1):
            pmerkit[i] = [{"sarake": i, "vari": "blue"}]
    elif kenosuunta == btt:
        for i in range(1, l_koko+1):
            pmerkit[i] = [{"sarake": l_koko+1-i, "vari": "blue"}]
    else:
        return pmerkit
    
    return pmerkit

#pelimerkin poisto
def poista_merkki(pmerkit, poistettu):
    if not poistettu:
        return pmerkit
    avain = str(poistettu.split(":")[0])
    arvo = str(poistettu.split(":")[1])
    for k in pmerkit[avain]:
        if k["sarake"] == int(arvo):
            pmerkit[avain].remove(k)
    return pmerkit

#poistetun palautus(punaisena)
def palauta_ed(pmerkit, rivi_kumottava, sarake_kumottava):
    for rivi in pmerkit:
        if int(rivi) == rivi_kumottava:
            pmerkit[rivi].append({"sarake": sarake_kumottava, "vari": "red"})
    return pmerkit

