"""Gera data/samples/copa2026_players.json com elencos de todas as 48 selecoes (26 por time).
Execute: python scripts/bootstrap_copa2026_players.py
"""
from __future__ import annotations

import json
import random
from pathlib import Path

random.seed(2026)
OUT = Path("data/samples/copa2026_players.json")

KEY_PLAYERS: dict[str, list[tuple]] = {
    "T-MEX": [("Guillermo Ochoa","GK",40,81,56,17,70,67,81,74,0,0,3),("Santiago Gimenez","ST",24,82,82,83,70,78,44,80,3,0,4),("Hirving Lozano","RW",30,81,88,76,78,82,44,74,1,2,4),("Edson Alvarez","CDM",27,81,75,64,79,76,84,83,0,1,4),("Alexis Vega","CAM",27,79,82,75,80,80,52,73,1,1,4),("Cesar Montes","CB",28,78,71,43,72,70,84,82,0,0,4),("Andres Guardado","CM",37,76,68,70,82,74,74,70,0,1,4),("Raul Jimenez","ST",33,78,76,79,66,73,42,78,1,0,3)],
    "T-RSA": [("Ronwen Williams","GK",33,78,55,16,69,66,78,73,0,0,3),("Percy Tau","LW",31,78,86,72,77,81,45,72,0,1,3),("Themba Zwane","CAM",33,77,80,73,79,78,50,71,1,0,3),("Bongani Zungu","CM",30,75,73,66,77,73,75,78,0,0,3)],
    "T-KOR": [("Son Heung-min","LW",34,87,88,83,82,86,50,74,2,2,3),("Lee Kang-in","CAM",23,83,82,79,84,83,58,73,1,1,3),("Kim Min-jae","CB",28,85,78,44,75,74,90,85,0,0,3),("Hwang Hee-chan","ST",28,80,87,78,74,79,46,77,1,0,3)],
    "T-CZE": [("Tomas Soucek","CM",30,80,73,74,80,75,79,84,0,0,3),("Patrik Schick","ST",29,82,76,84,72,77,42,80,1,0,3),("Vladimir Coufal","RB",32,77,82,65,76,76,77,77,0,0,3)],
    "T-CAN": [("Alphonso Davies","LB",24,84,97,63,76,83,76,77,0,2,4),("Jonathan David","ST",25,83,81,84,72,78,44,78,2,1,4),("Cyle Larin","ST",30,78,80,79,68,74,43,80,1,0,4),("Milan Borjan","GK",37,78,55,16,69,66,78,74,0,0,4),("Tajon Buchanan","RW",24,79,91,72,75,80,47,72,0,1,4),("Atiba Hutchinson","CM",41,73,64,64,78,73,72,76,0,0,4),("Kamal Miller","CB",28,77,74,42,72,70,82,80,0,0,4)],
    "T-BIH": [("Edin Dzeko","ST",38,78,74,80,71,74,38,79,1,1,3),("Sead Kolasinac","LB",31,76,76,54,72,69,77,82,0,0,3)],
    "T-SUI": [("Granit Xhaka","CM",32,84,69,74,86,81,82,79,0,2,4),("Xherdan Shaqiri","RW",33,79,80,76,79,78,47,73,1,2,4),("Manuel Akanji","CB",29,84,78,43,75,74,88,83,0,0,4),("Yann Sommer","GK",36,84,57,17,73,72,84,74,0,0,4),("Ruben Vargas","LW",26,79,84,73,79,79,55,72,1,1,4),("Remo Freuler","CM",32,79,73,71,80,77,76,78,0,1,4),("Fabian Schar","CB",33,80,76,50,74,73,84,80,0,0,4),("Noah Okafor","ST",25,79,88,76,74,79,47,75,1,0,3)],
    "T-QAT": [("Akram Afif","LW",28,79,86,72,77,81,48,72,1,1,3),("Almoez Ali","ST",27,77,80,76,67,73,42,76,1,0,3),("Hassan Al-Haydos","RW",32,76,79,71,75,76,46,70,0,1,2),("Meshaal Barsham","GK",25,76,55,16,67,64,76,72,0,0,3)],
    "T-BRA": [("Alisson Becker","GK",32,89,57,17,78,75,89,79,0,0,4),("Marquinhos","CB",30,88,74,46,79,78,90,79,0,0,4),("Vinicius Jr.","LW",24,91,96,83,77,92,49,75,2,2,4),("Rodrygo","RW",24,87,88,83,83,88,54,73,1,1,4),("Endrick","ST",19,83,86,84,72,82,46,78,1,0,4),("Casemiro","CDM",33,84,73,72,82,79,86,85,0,1,4),("Bruno Guimaraes","CM",27,86,80,74,86,83,78,82,0,2,4),("Richarlison","CF",27,83,84,80,74,82,50,82,0,0,4),("Danilo","RB",33,81,80,66,79,79,79,79,0,1,4),("Eder Militao","CB",26,86,82,48,76,77,89,82,0,0,4),("Raphinha","RW",28,85,88,80,81,85,54,72,1,0,4),("Renan Lodi","LB",27,79,84,60,76,76,77,76,0,0,3)],
    "T-MAR": [("Yassine Bounou","GK",34,84,56,16,71,68,84,73,0,0,5),("Achraf Hakimi","RB",26,84,92,74,81,84,77,79,1,3,5),("Youssef En-Nesyri","ST",27,82,79,83,63,75,42,83,3,1,5),("Hakim Ziyech","RW",32,81,76,79,84,83,45,71,1,2,5),("Sofyan Amrabat","CM",28,81,77,67,81,79,84,83,0,1,5),("Romain Saiss","CB",35,79,70,44,73,71,84,80,0,0,5),("Noussair Mazraoui","RB",27,80,82,65,77,78,78,76,0,1,5),("Azzedine Ounahi","CM",24,78,80,68,79,78,69,75,0,1,5),("Sofiane Boufal","LW",30,79,82,74,79,81,48,71,1,2,5),("Amine Harit","CAM",27,78,79,72,79,79,52,72,0,1,4)],
    "T-HAI": [("Duckens Nazon","ST",32,73,80,71,65,71,40,74,0,0,3)],
    "T-SCO": [("Andy Robertson","LB",32,83,85,62,82,80,79,76,0,1,3),("Scott McTominay","CM",27,80,74,74,78,77,78,85,0,0,3),("Che Adams","ST",28,77,80,75,68,74,44,77,1,0,3),("Craig Gordon","GK",41,77,55,16,69,66,77,73,0,0,3),("John McGinn","CM",30,79,76,73,79,76,73,80,0,0,3)],
    "T-USA": [("Christian Pulisic","CAM",26,84,84,80,83,84,57,74,2,2,4),("Tyler Adams","CDM",26,82,79,67,82,78,82,82,0,1,4),("Weston McKennie","CM",27,80,77,74,79,77,77,83,1,0,4),("Gio Reyna","CAM",23,80,82,76,82,82,55,70,1,1,4),("Matt Turner","GK",31,79,57,16,70,67,79,76,0,0,4),("Antonee Robinson","LB",27,79,87,58,75,76,76,75,0,1,4),("Walker Zimmermann","CB",31,77,72,43,71,70,82,80,0,0,4),("Ricardo Pepi","ST",22,77,82,76,68,74,42,76,1,0,4),("Yunus Musah","CM",22,79,82,70,78,79,66,76,0,1,4),("Sergiño Dest","RB",24,78,87,64,75,77,74,73,0,1,4),("Tim Weah","RW",24,79,88,72,75,80,47,73,0,1,4)],
    "T-PAR": [("Miguel Almiron","CAM",30,80,83,74,81,82,56,74,0,1,4),("Antonio Sanabria","ST",29,79,78,79,67,74,42,78,0,1,4),("Gustavo Gomez","CB",31,80,72,44,72,70,85,82,0,0,4),("Angel Romero","RW",31,78,81,74,76,78,48,72,1,0,4),("Antony Silva","GK",36,77,55,16,68,65,77,73,0,0,4)],
    "T-AUS": [("Mathew Ryan","GK",33,80,56,17,71,68,80,74,0,0,4),("Mitchell Duke","ST",33,76,79,74,65,71,41,75,1,0,4),("Aaron Mooy","CM",34,78,71,71,79,75,74,74,0,1,4),("Martin Boyle","RW",31,75,86,68,72,75,45,70,0,1,4),("Harry Souttar","CB",25,80,72,44,72,70,84,85,0,0,4)],
    "T-TUR": [("Arda Guler","CAM",20,82,83,79,82,83,56,70,1,1,4),("Hakan Calhanoglu","CM",30,84,73,80,87,83,73,76,1,2,4),("Kenan Yildiz","RW",20,80,86,74,77,81,50,71,1,0,4),("Ugurcan Cakir","GK",28,79,56,17,70,67,79,73,0,0,4),("Merih Demiral","CB",26,82,76,44,73,72,87,83,0,0,4),("Cenk Tosun","ST",33,76,74,76,66,71,42,78,2,0,4)],
    "T-GER": [("Manuel Neuer","GK",40,85,57,18,78,74,85,76,0,0,4),("Joshua Kimmich","CDM",30,87,76,76,90,85,85,76,0,2,4),("Jamal Musiala","CAM",22,89,87,84,88,90,67,72,4,2,4),("Florian Wirtz","CAM",22,88,84,82,88,89,63,72,2,3,4),("Kai Havertz","CF",26,85,82,82,83,82,64,80,3,1,4),("Leroy Sane","RW",29,86,93,80,83,87,52,73,2,1,4),("Ilkay Gundogan","CM",36,84,73,77,88,85,70,73,0,2,4),("Niklas Sule","CB",29,83,76,44,74,73,88,88,0,0,4),("Antonio Rudiger","CB",31,83,79,47,73,73,89,86,0,0,4),("Thomas Muller","CF",37,82,75,76,84,83,62,72,0,2,4),("Julian Brandt","CAM",28,82,78,77,84,82,65,71,0,1,3)],
    "T-CIV": [("Sebastien Haller","ST",30,79,78,79,68,74,42,82,1,0,3),("Franck Kessie","CM",28,82,76,74,82,80,76,85,0,1,3),("Nicolas Pepe","RW",30,79,88,75,79,82,46,72,1,0,3),("Serge Aurier","RB",32,77,82,64,74,74,76,77,0,1,3)],
    "T-ECU": [("Enner Valencia","ST",35,79,78,79,68,74,42,78,2,1,3),("Moises Caicedo","CDM",22,82,78,67,82,78,82,82,0,2,3),("Pervis Estupinan","LB",26,81,88,62,78,79,79,77,0,1,3),("Gonzalo Plata","RW",24,78,88,72,75,79,46,72,1,0,3)],
    "T-CUW": [("Jurien Timber","CB",22,78,78,50,74,73,82,78,0,0,2),("Leandro Bacuna","CM",33,72,71,65,72,70,72,76,0,0,2)],
    "T-NED": [("Virgil van Dijk","CB",35,88,77,44,76,76,92,86,0,0,3),("Frenkie de Jong","CM",29,87,79,72,87,84,75,76,0,2,3),("Cody Gakpo","LW",25,83,86,78,79,83,52,76,1,1,3),("Xavi Simons","CAM",23,83,84,78,83,84,58,72,1,1,3),("Bart Verbruggen","GK",22,80,56,17,70,67,80,73,0,0,3),("Denzel Dumfries","RB",28,82,88,67,77,79,78,82,0,2,3),("Memphis Depay","ST",30,83,85,83,80,83,46,76,2,0,3),("Nathan Ake","CB",30,82,78,48,76,74,86,81,0,0,3),("Wout Weghorst","ST",32,78,76,76,67,71,48,84,1,0,3)],
    "T-JPN": [("Takefusa Kubo","RW",23,84,88,78,80,86,52,71,2,1,3),("Kaoru Mitoma","LW",27,83,90,75,79,85,49,70,1,2,3),("Wataru Endo","CDM",31,80,72,67,79,76,82,79,0,1,3),("Maya Yoshida","CB",36,76,68,44,73,71,82,79,0,0,3),("Shuichi Gonda","GK",32,78,55,16,68,65,78,72,0,0,3)],
    "T-SWE": [("Alexander Isak","ST",25,84,89,84,74,82,46,79,3,1,3),("Dejan Kulusevski","RW",24,83,85,78,82,83,56,74,2,1,3),("Victor Lindelof","CB",30,80,74,46,74,73,85,79,0,0,3),("Emil Forsberg","CAM",33,79,79,76,81,78,56,70,0,2,3),("Robin Olsen","GK",34,78,55,16,69,66,78,73,0,0,3)],
    "T-TUN": [("Wahbi Khazri","CAM",33,76,77,72,77,75,49,71,0,1,3),("Youssef Msakni","LW",34,74,79,70,74,74,46,69,1,0,3),("Aymen Dahmen","GK",27,75,56,16,66,63,75,72,0,0,3)],
    "T-BEL": [("Kevin De Bruyne","CM",33,90,76,87,94,88,64,77,2,4,5),("Romelu Lukaku","ST",31,85,80,89,74,80,36,89,3,1,5),("Thibaut Courtois","GK",33,89,56,18,75,73,89,82,0,0,5),("Youri Tielemans","CM",28,83,74,79,85,82,73,75,1,2,5),("Jeremy Doku","LW",23,82,96,76,79,85,47,71,2,2,5),("Charles De Ketelaere","CAM",23,80,77,76,81,80,60,73,0,1,5),("Toby Alderweireld","CB",35,80,70,45,76,73,86,80,0,0,5),("Jan Vertonghen","CB",37,78,68,44,74,71,83,78,0,0,5),("Leandro Trossard","LW",30,81,84,76,80,80,52,72,1,1,5),("Amadou Onana","CM",23,80,78,69,78,77,77,84,0,0,5)],
    "T-EGY": [("Mohamed Salah","RW",33,89,90,89,82,87,45,76,3,2,4),("Trezeguet","LW",30,79,82,74,73,77,46,74,1,1,4),("Ahmed Hegazi","CB",34,79,64,37,67,70,83,83,0,0,4),("Mohamed Elneny","CM",32,78,72,66,79,74,76,74,0,1,4),("El-Shenawy","GK",38,77,55,16,68,65,77,72,0,0,4),("Omar Marmoush","ST",25,81,85,80,76,80,48,77,2,1,4),("Mostafa Mohamed","ST",24,78,81,77,69,74,42,77,1,0,4)],
    "T-IRN": [("Mehdi Taremi","ST",32,82,80,83,72,78,44,79,2,1,3),("Sardar Azmoun","ST",30,81,80,82,73,78,45,78,1,1,3),("Hossein Hosseini","GK",29,76,56,16,67,64,76,72,0,0,3)],
    "T-NZL": [("Chris Wood","ST",32,79,76,79,66,72,42,80,1,0,3),("Stefan Marinovic","GK",33,74,55,15,65,62,74,70,0,0,3)],
    "T-ESP": [("Marc-Andre ter Stegen","GK",33,87,58,17,76,73,87,74,0,0,4),("Lamine Yamal","RW",18,90,91,84,87,93,42,69,3,3,4),("Rodri","CDM",29,91,70,74,91,86,88,82,0,2,4),("Pedri","CM",23,88,82,79,89,89,72,72,1,2,4),("Nico Williams","LW",23,87,93,80,83,89,50,73,2,2,4),("Dani Olmo","CAM",27,85,82,80,86,85,67,74,2,2,4),("Alvaro Morata","ST",32,83,83,82,77,79,50,80,2,1,4),("Alejandro Grimaldo","LB",29,83,85,62,82,80,78,74,0,2,4),("Aymeric Laporte","CB",30,83,74,48,77,75,87,79,0,0,4),("Dani Carvajal","RB",32,82,79,64,78,76,80,79,0,1,4),("Gavi","CM",20,84,79,72,86,84,72,71,0,1,4)],
    "T-KSA": [("Mohammad Al-Owais","GK",30,76,56,16,67,64,76,72,0,0,3),("Salem Al-Dawsari","LW",32,78,82,73,76,78,48,71,1,0,3)],
    "T-URU": [("Darwin Nunez","ST",25,84,93,82,70,80,43,82,2,0,3),("Rodrigo Bentancur","CM",27,82,79,73,83,80,76,80,0,1,3),("Luis Suarez","ST",39,80,75,83,77,78,36,75,1,1,3),("Sergio Rochet","GK",29,78,56,17,69,66,78,73,0,0,3),("Ronald Araujo","CB",25,84,79,47,74,73,89,84,0,0,3),("Jose Maria Gimenez","CB",30,82,77,45,74,72,87,82,0,0,3)],
    "T-CPV": [("Djaniny","ST",33,75,81,72,64,71,40,74,1,1,3),("Nuno Tavares","LB",24,76,85,58,74,74,74,72,0,1,3)],
    "T-FRA": [("Mike Maignan","GK",29,88,56,17,74,70,88,79,0,0,6),("Kylian Mbappe","ST",26,91,97,93,82,93,45,78,4,2,6),("Antoine Griezmann","CF",35,85,79,87,88,85,62,74,2,2,6),("Eduardo Camavinga","CM",22,85,84,74,85,86,80,82,0,1,6),("Theo Hernandez","LB",27,84,87,71,79,82,75,83,1,1,6),("William Saliba","CB",23,84,80,44,76,75,88,83,0,0,6),("Aurelien Tchouameni","CDM",24,84,78,72,83,81,83,83,0,1,6),("Marcus Thuram","ST",27,84,87,81,77,82,47,80,2,1,6),("Jules Kounde","RB",26,83,82,67,79,80,83,77,0,1,6),("Raphael Varane","CB",31,83,79,47,76,74,88,80,0,0,6),("Ousmane Dembele","RW",28,84,92,79,80,86,50,72,1,2,6),("Christopher Nkunku","CF",27,85,85,82,82,85,59,77,1,1,6),("Adrien Rabiot","CM",31,81,79,73,82,78,74,82,0,1,6)],
    "T-SEN": [("Edouard Mendy","GK",32,82,56,17,71,68,82,74,0,0,3),("Sadio Mane","LW",32,86,90,84,78,86,47,74,2,2,3),("Kalidou Koulibaly","CB",33,85,76,46,74,73,89,85,0,0,3),("Ismaila Sarr","RW",27,82,92,77,76,82,48,75,1,1,3),("Idrissa Gueye","CDM",35,80,76,66,80,76,82,80,0,0,3)],
    "T-IRQ": [("Amjed Attwan","CM",28,73,70,65,73,70,71,73,0,0,3)],
    "T-NOR": [("Orjan Nyland","GK",34,80,55,15,72,72,80,75,0,0,5),("Erling Haaland","ST",25,94,89,97,66,80,45,88,4,1,5),("Martin Odegaard","CAM",27,88,81,81,89,89,59,72,1,3,5),("Alexander Sorloth","ST",29,82,76,83,71,73,46,84,2,1,5),("Sander Berge","CM",26,82,74,73,82,80,78,82,0,2,5),("Mohamed Elyounoussi","LW",30,79,83,73,77,79,52,72,1,1,5),("Leo Skiri Ostigard","CB",24,79,74,45,73,72,83,80,0,0,5),("Kristian Thorstvedt","CM",24,78,79,70,79,77,68,76,0,1,5),("Antonio Nusa","LW",20,79,88,73,76,80,48,70,1,0,5)],
    "T-ARG": [("Emiliano Martinez","GK",32,89,56,18,73,70,88,79,0,0,4),("Lionel Messi","RW",38,90,82,88,92,94,34,65,3,4,4),("Julian Alvarez","ST",25,86,83,86,81,85,53,79,2,1,4),("Alexis Mac Allister","CM",26,86,78,78,86,83,79,79,0,2,4),("Rodrigo De Paul","CM",30,85,79,77,86,82,74,80,0,1,4),("Enzo Fernandez","CM",23,84,78,74,84,81,74,76,0,1,4),("Nicolas Otamendi","CB",36,82,73,46,74,72,87,82,0,0,4),("Cristian Romero","CB",26,84,80,48,76,74,88,83,0,0,4),("Nicolas Tagliafico","LB",32,80,82,62,79,77,79,76,0,1,4),("Nahuel Molina","RB",27,80,85,65,76,77,78,76,0,2,4),("Angel Di Maria","RW",37,84,85,79,83,83,49,71,1,2,4),("Lautaro Martinez","ST",27,87,83,87,80,85,52,81,2,1,4),("Paulo Dybala","CF",32,83,82,82,83,83,50,75,0,1,3)],
    "T-ALG": [("Riyad Mahrez","RW",35,83,83,79,83,83,48,71,0,2,3),("Yacine Brahimi","LW",34,79,84,73,79,80,48,71,1,1,3),("Islam Slimani","ST",36,76,74,76,66,71,40,77,2,0,3),("Rais M Bolhi","GK",38,75,55,15,66,63,75,71,0,0,3)],
    "T-AUT": [("David Alaba","CB",33,82,78,58,80,78,86,79,0,1,4),("Marcel Sabitzer","CM",30,81,77,75,82,79,73,78,1,1,4),("Marko Arnautovic","ST",37,79,76,78,71,73,38,78,2,0,4),("Patrick Pentz","GK",27,77,55,16,67,64,77,72,0,0,4),("Florian Grillitsch","CM",30,78,73,69,78,75,75,77,0,0,4)],
    "T-JOR": [("Baha Faisal","CM",27,73,71,64,72,70,71,72,0,0,3)],
    "T-POR": [("Diogo Costa","GK",26,85,57,17,74,72,85,74,0,0,4),("Cristiano Ronaldo","ST",41,86,81,92,80,85,34,76,3,1,4),("Bruno Fernandes","CAM",30,88,78,85,90,88,63,76,2,3,4),("Ruben Dias","CB",28,88,72,39,74,74,91,85,0,0,4),("Bernardo Silva","CM",30,87,81,78,89,88,68,75,1,2,4),("Vitinha","CM",25,85,79,74,86,83,72,73,0,2,4),("Joao Cancelo","RB",30,84,85,68,82,82,80,76,0,2,4),("Rafael Leao","LW",25,85,94,80,79,86,52,74,2,1,4),("Goncalo Ramos","ST",23,82,81,83,75,79,48,76,1,0,4),("Ruben Neves","CDM",28,82,74,74,83,80,80,77,0,1,4),("Nuno Mendes","LB",22,82,87,63,78,78,77,74,0,1,4),("Joao Felix","LW",25,83,83,79,83,83,52,72,1,1,4)],
    "T-COD": [("Cedric Bakambu","ST",33,76,78,75,65,71,41,75,1,0,3),("Chancel Mbemba","CB",30,77,74,44,71,70,82,80,0,0,3)],
    "T-UZB": [("Eldor Shomurodov","ST",29,77,78,76,65,71,42,76,1,0,3),("Jasur Yakhshiboev","CM",26,73,71,65,72,70,71,73,0,1,2)],
    "T-COL": [("David Ospina","GK",36,80,55,17,71,68,80,73,0,0,4),("James Rodriguez","CAM",34,83,72,82,91,84,43,69,1,3,4),("Luis Diaz","LW",28,85,90,79,80,85,50,75,2,2,4),("Jhon Duran","ST",21,82,83,83,70,78,47,84,1,0,4),("Davinson Sanchez","CB",28,82,79,44,72,72,87,84,0,0,4),("Yerry Mina","CB",30,80,74,44,72,70,85,84,0,0,4),("Juan Cuadrado","RW",36,79,82,73,77,78,50,72,0,1,4),("Richard Rios","CM",24,78,77,68,78,76,70,77,0,1,4),("Mateus Uribe","CM",33,77,72,71,78,74,73,77,0,0,4)],
    "T-ENG": [("Jordan Pickford","GK",32,84,56,18,73,70,84,73,0,0,5),("Jude Bellingham","CAM",21,91,83,85,90,91,73,83,3,2,5),("Harry Kane","ST",31,88,71,91,86,85,47,85,3,1,5),("Bukayo Saka","RW",23,88,88,81,85,88,65,73,2,2,5),("Phil Foden","CM",25,88,83,83,88,88,66,72,1,1,5),("Trent Alexander-Arnold","RB",26,87,81,76,90,83,73,74,0,2,5),("Declan Rice","CDM",26,85,77,71,84,81,83,84,0,1,5),("Harry Maguire","CB",33,81,71,46,74,72,86,84,0,0,5),("John Stones","CB",30,83,77,48,77,74,87,79,0,0,5),("Marcus Rashford","LW",27,85,91,80,75,84,52,76,2,1,5),("Cole Palmer","CAM",22,83,79,79,84,82,60,72,1,1,5)],
    "T-CRO": [("Luka Modric","CM",39,87,74,72,91,86,61,70,0,2,3),("Ivan Perisic","LW",35,82,84,75,79,81,54,79,1,1,3),("Mateo Kovacic","CM",30,84,81,71,86,82,72,74,0,1,3),("Ante Budimir","ST",33,78,76,78,67,72,43,78,2,0,3),("Josko Gvardiol","CB",23,83,80,49,75,74,87,82,0,0,3),("Dominik Livakovic","GK",29,81,56,17,70,67,81,73,0,0,3)],
    "T-GHA": [("Thomas Partey","CDM",31,83,77,72,83,80,82,82,0,1,3),("Jordan Ayew","ST",32,78,82,73,74,76,46,74,1,0,3),("Inaki Williams","ST",30,80,91,74,74,80,48,76,1,0,3),("Lawrence Ati-Zigi","GK",28,76,56,16,67,64,76,72,0,0,3)],
    "T-PAN": [("Rolando Blackburn","ST",31,73,76,70,62,67,38,71,0,0,3),("Adalberto Carrasquilla","CM",27,74,72,67,74,71,70,73,0,1,2)],
}

DEPTH_NAMES: dict[str, list[str]] = {
    "T-MEX":["Carlos","Miguel","Jorge","Luis","Angel"],
    "T-RSA":["Sipho","Thabo","Siyanda","Andile","Bongani"],
    "T-KOR":["Junho","Sangmin","Jaesung","Hyunwoo","Seunghyun"],
    "T-CZE":["Tomas","Jakub","David","Jiri","Lukas"],
    "T-CAN":["Jonathan","Stefan","Atiba","Scott","Samuel"],
    "T-BIH":["Haris","Amer","Jusuf","Armin","Aldin"],
    "T-SUI":["Silvan","Denis","Nico","Cedric","Steven"],
    "T-QAT":["Hassan","Karimi","Boudiaf","Ahmad","Sultan"],
    "T-BRA":["Eder","Alex","Felipe","Gerson","Gabriel","Weverton","Bremer","Pedro"],
    "T-MAR":["Selim","Ilias","Zakaria","Walid","Bilal","Mehdi","Nassim","Tariq"],
    "T-HAI":["Wilde","Carlo","Franky","Kervens","Steeven","Jeffry"],
    "T-SCO":["James","Stuart","Ryan","Barry","Stephen","Grant"],
    "T-USA":["Caleb","Jordan","Miles","Gaga","Johnny","George"],
    "T-PAR":["Braian","Jorge","Pablo","Ivan","Diego","Richard"],
    "T-AUS":["Nick","Mark","Jackson","Bailey","Elijah","Ben"],
    "T-TUR":["Mert","Burak","Ozan","Emre","Baris","Salih"],
    "T-GER":["Leon","Jonas","Robin","Nico","Maximilian","Karim"],
    "T-CIV":["Wilfried","Maxwel","Armand","Willy","Kouadio","Lacina"],
    "T-ECU":["Jhegson","Angelo","Piero","Junior","Jordy","Jeremy"],
    "T-CUW":["Gilson","Darryl","Elson","Tyler","Leandro","Shane"],
    "T-NED":["Noa","Jurrien","Matthijs","Brian","Teun","Stefan"],
    "T-JPN":["Hiroki","Daichi","Kengo","Yusuke","Shoya","Ritsu","Koki"],
    "T-SWE":["Linus","Pontus","Marcus","Jesper","Joel","Oscar"],
    "T-TUN":["Naim","Hamza","Anis","Ghailene","Amine","Ellyes"],
    "T-BEL":["Lois","Alexis","Dodi","Timothy","Wout","Hannes"],
    "T-EGY":["Ramadan","Ahmed","Maged","Kahraba","Mahmoud","Akram"],
    "T-IRN":["Saeid","Alireza","Omid","Rouzbeh","Morteza","Kaveh"],
    "T-NZL":["Winston","Tommy","Clayton","Storm","Michael","Kosta"],
    "T-ESP":["Eric","Borja","Unai","Joselu","Marco","Jesus","Mikel"],
    "T-KSA":["Yasser","Firas","Sultan","Turki","Hattan","Nasser"],
    "T-URU":["Brian","Gaston","Nahitan","Facundo","Maxi","Federico"],
    "T-CPV":["Ryan","Jair","Jamiro","Nanu","Garry","Kevin"],
    "T-FRA":["Theo","Benjamin","Randal","Kingsley","Axel","Hugo","Ferland"],
    "T-SEN":["Formose","Alfred","Krepin","Cheikhou","Mamadou","Boulaye"],
    "T-IRQ":["Bashar","Ali","Mohannad","Saad","Ahmed","Omar"],
    "T-NOR":["Jonas","Jorgen","Ole","Tobias","Hakon","Markus","Sondre"],
    "T-ARG":["German","Walter","Federico","Guido","Exequiel","Thiago"],
    "T-ALG":["Nassim","Zinedine","Ryad","Ramiz","Farid","Soufiane"],
    "T-AUT":["Michael","Andreas","Philipp","Valentino","Dejan","Marco"],
    "T-JOR":["Yahia","Ahmad","Yazan","Mohammad","Hussain","Anas"],
    "T-POR":["Goncalo","Diogo","Joao","Francisco","Andre","Pedro","Nelson"],
    "T-COD":["Yannick","Yves","Theo","Heritier","Ben","Merveille"],
    "T-UZB":["Javokhir","Otabek","Sherzod","Sanjar","Dostonbek","Bekhzod"],
    "T-COL":["Rafael","Cucho","Teo","Wilmar","Oscar","Jorman"],
    "T-ENG":["Conor","Harvey","Anthony","Aaron","Callum","James","Tyler"],
    "T-CRO":["Borna","Duje","Ivan","Lovro","Kristijan","Martin"],
    "T-GHA":["Joseph","Felix","Richmond","Mohammed","Abdul","Kelvin"],
    "T-PAN":["Anibal","Edgar","Eric","Alberto","Ivan","Fidel"],
}

def _gen(base, sigma=4):
    return max(60, min(85, base + round(random.gauss(0, sigma))))

def _depth(team_id, pos, idx, base):
    names = DEPTH_NAMES.get(team_id, ["Player"])
    nm = names[idx % len(names)] + " " + chr(65 + idx % 26)
    age = random.randint(21, 34)
    o = _gen(base)
    if pos == "GK":
        return (nm,pos,age,o,random.randint(55,60),15,_gen(68,4),_gen(62,4),_gen(o-2,3),_gen(o-4,3),0,0,0)
    if pos in ("CB","RB","LB"):
        return (nm,pos,age,o,_gen(72,6),random.randint(38,55),_gen(70,5),_gen(65,5),_gen(o-6,3),_gen(75,6),0,0,0)
    if pos in ("CDM","CM"):
        return (nm,pos,age,o,_gen(70,5),_gen(65,5),_gen(o-3,4),_gen(72,5),_gen(70,5),_gen(75,5),0,0,0)
    return (nm,pos,age,o,_gen(82,6),_gen(o-5,5),_gen(74,5),_gen(o-4,5),_gen(42,8),_gen(72,6),0,0,0)

def build_squad(tid, keys):
    records = []
    used = {}
    suffix = {}
    for row in keys:
        nm,pos,age,o,pac,sho,pas,dri,dff,phy,cg,ca,cm = row
        pid = f"P-{tid[2:]}-{nm.split()[0][:4].upper()}{age}"
        suffix[pid] = suffix.get(pid,0); suffix[pid]+=1
        if suffix[pid]>1: pid+=str(suffix[pid])
        records.append(dict(player_id=pid,name=nm,team_id=tid,position=pos,age=age,
                            overall=o,pace=pac,shooting=sho,passing=pas,dribbling=dri,
                            defending=dff,physical=phy,copa_goals=cg,copa_assists=ca,
                            copa_matches=cm,source="ea_fc25_community",snapshot_id="copa2026-07-06"))
        used[pos] = used.get(pos,0)+1
    GOALS = {"GK":3,"CB":5,"RB":2,"LB":2,"CDM":2,"CM":3,"CAM":2,"RW":2,"LW":2,"ST":3,"CF":0}
    BASES = {"GK":74,"CB":72,"RB":72,"LB":72,"CDM":73,"CM":73,"CAM":73,"RW":73,"LW":73,"ST":74,"CF":73}
    for pos,goal in GOALS.items():
        curr = used.get(pos,0)
        for i in range(goal - curr):
            if len(records) >= 26: break
            row = _depth(tid, pos, len(records)+i, BASES.get(pos,73))
            nm=row[0]; pid=f"P-{tid[2:]}-{nm.split()[0][:4].upper()}{row[2]}"
            suffix[pid]=suffix.get(pid,0); suffix[pid]+=1
            if suffix[pid]>1: pid+=str(suffix[pid])
            records.append(dict(player_id=pid,name=nm,team_id=tid,position=pos,age=row[2],
                                overall=row[3],pace=row[4],shooting=row[5],passing=row[6],
                                dribbling=row[7],defending=row[8],physical=row[9],
                                copa_goals=row[10],copa_assists=row[11],copa_matches=row[12],
                                source="ea_fc25_community",snapshot_id="copa2026-07-06"))
        if len(records) >= 26: break
    return records[:26]

def main():
    all_players = []
    for tid,keys in KEY_PLAYERS.items():
        all_players.extend(build_squad(tid,keys))
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(all_players,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Gerados: {len(all_players)} jogadores de {len(KEY_PLAYERS)} selecoes")
    top = sorted(all_players, key=lambda p: p["copa_goals"], reverse=True)[:8]
    print("Top artilheiros:")
    for p in top:
        print(f"  {p['copa_goals']}g  {p['name']} ({p['team_id']}) OVR {p['overall']}")

if __name__=="__main__":
    main()
