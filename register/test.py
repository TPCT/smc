import random

case = """
<case>
    <ssn>#ssn#</ssn>
    <firstName>محمد</firstName>
    <secondName>عبد الله</secondName>
    <thirdName>محمد</thirdName>
    <fourthName>مصطفى</fourthName>
    <city>أبنوب</city>
    <address>شارع ابنوب</address>
    <phoneNumber>0</phoneNumber>
    <governorate>
        <option checked="1" value="25">أسيوط</option>
    </governorate>
    <MaritalStatus>
        <option checked="1" value="2">أعزب</option>
    </MaritalStatus>
    <Job>
        <option checked="1" value="56">بدون عمل</option>
    </Job>
    <ddl>
        <option checked="1" value="1">إعاقة حركية</option>
    </ddl>
    <note>تجربة</note>
</case>
"""

for i in range(50):
    with open(f"register_cases/alexandria/case{i}.xml", 'w+') as case_writer:
        case_writer.write(case.replace("#ssn#", str(random.randint(29412032500000, 29412032599999))))