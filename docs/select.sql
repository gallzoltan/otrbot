select 
    jb.ksh, 
    onk.onev, 
    SUBSTR(st.torzs_sz||'-'||st.afakod||'-'||st.mk, 0, 8) as torzsszam,
    jb.ttamogat,
    jb.tamogft, 
    jb.nev, 
    cim.irszam,
    cim.koztnev||' '||cim.kozjell as cim,
    cim.hsz1 as hsz,
    TRIM(REPLACE(rk.megnevezes, 'i Régió')) as regio, 
    tk.tamogcel, 
    t.aht, 
    jb.utdatum,
    jb.okirat,
    jb.ebr42,
    jb.jobleir
from wirgilsys.vw_alljob_n jb
left join SUPPORTSYS.t_onkorm_tech onk on onk.ksh=jb.ksh
left join (select * from SUPPORTSYS.t_stat) st on st.ksh=jb.ksh
left join (select * from SUPPORTSYS.t_cim) cim on cim.ksh=jb.ksh
left join SUPPORTSYS.t_regio rk on rk.regiokod=onk.rk
left join (select * from SUPPORTSYS.t_tamogat where ev=:ev) t on t.tamogat=jb.ttamogat
left join (select * from SUPPORTSYS.t_tamogat_kieg where ev=:ev) tk on tk.tamogat=jb.ttamogat
where jb.ev=:ev 
    and jb.ttamogat in ('0902010541', '0902010542', '0902010550', '0902010560')
order by jb.ebr42, jb.okirat;