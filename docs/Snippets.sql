

 mysql -h lala -u EMSro --password=eh3sJUWemvb9   EMSdata

select * from Ctr_1526476850_PV_Erzeugung where value=2441;
Ctr_1532951436_PV_DC_Seitig

grep 2441 *global_11_27_2020.txt
pv_global_1526476850_global_11_27_2020.txt:1606477542;2441


--system-time-zone


select 
    Ctr_1526476850_PV_Erzeugung.time as time,
    Ctr_1526476850_PV_Erzeugung.value-Ctr_1532951436_PV_DC_Seitig.value as "WR1"
from Ctr_1526476850_PV_Erzeugung 
left join Ctr_1532951436_PV_DC_Seitig 
    on Ctr_1526476850_PV_Erzeugung.time = Ctr_1532951436_PV_DC_Seitig.time
where  
    $__timeFilter(time)
ORDER BY time




SELECT
  time AS "time",
  value AS "DC-Seitig"
FROM Ctr_1532951436_PV_DC_Seitig
WHERE
  $__timeFilter(time)
ORDER BY time