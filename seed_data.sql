-- Insert data into the Users table
COPY public.users (id, username, password_hash) FROM stdin;
1	Gus	scrypt:32768:8:1$mcnB9BJNcllvltBH$eb5177946fde690f59490222648985547c2b4f0193d06520a7ac1f282ea439f3314cf049ff41cf912717c7dcb140b3caf64419e3699bf1736a5e687c8866c3b9
\.

-- Insert data into the Person table
COPY public.person (id, user_id, name) FROM stdin;
1	1	Lauren
2	1	Colton
3	1	Cesar
4	1	Tim
5	1	Denise
6	1	Simone
7	1	Amin
8	1	Fred
\.

-- Insert data into the Gift table
COPY public.gift (id, person_id, gift) FROM stdin;
1103	1	Cozy throw blanket
1104	1	Gift certificate to a local cafe or restaurant
1105	1	Luxurious bath products
1106	1	New book by a favorite author or in a preferred genre
1107	1	Personalized journal and a nice pen
1108	1	Piece of jewelry (necklace, earrings, bracelet)
1109	1	Reusable water bottle or travel mug
1110	1	Scented candle or diffuser
1111	1	Subscription box (tailored to interests)
1112	1	Tickets to a local event or experience
1113	2	A DIY kit for something he might enjoy building (e.g., model car, terrarium)
1114	2	A book on a topic he's interested in (history, science fiction, etc.)
1115	2	A collection of craft beers or a bottle of his favorite spirit
1116	2	A comfortable and stylish t-shirt or hoodie
1117	2	A comfortable gaming headset or accessory
1118	2	A comfortable pair of noise-canceling headphones
1119	2	A cool gadget or tech accessory
1120	2	A donation to his favorite charity in his name
1121	2	A durable and stylish backpack
1122	2	A gift certificate for a massage or other relaxing experience
1123	2	A gift certificate to a local brewery or coffee shop
1124	2	A high-quality multi-tool
1125	2	A nice watch or a smartwatch
1126	2	A personalized piece of artwork or a framed print
1127	2	A portable Bluetooth speaker
1128	2	A set of gourmet snacks or his favorite treats
1129	2	A set of grilling tools or accessories
1130	2	A subscription box tailored to a hobby (e.g., coffee, grooming, outdoor gear)
1131	2	A subscription to a streaming service he'd enjoy
1132	2	Tickets to a sporting event or concert
1133	3	A book of photography or art that aligns with his taste
1134	3	A comfortable eye mask and earplugs for better sleep
1135	3	A comfortable pair of slippers for around the house
1136	3	A cool desk organizer or gadget
1137	3	A framed map of a place he loves or wants to visit
1138	3	A gift certificate for online gaming credits or a new video game
1139	3	A high-quality pocket knife
1140	3	A portable phone charger or power bank
1141	3	A selection of artisanal coffee beans or teas
1142	3	A selection of hot sauces or gourmet condiments
1143	3	A set of interesting board games or card games
1144	3	A set of quality pens or a notebook for journaling
1145	3	A small indoor plant or succulent
1146	3	A stylish and durable wallet
1147	3	A subscription to a magazine related to his interests
1148	4	A coffee mug
1149	4	A hooded jacket
1150	4	A long-sleeve t-shirt
1151	4	A retro 90s fan tee
1152	4	A travel mug gift set
1153	5	Wireless charging dock
1154	5	Fitness tracker
1155	5	Travel pillow
1156	6	Art supplies kit
1157	6	Portable coffee maker
1158	6	Board game
1159	7	Leather backpack
1160	7	Digital photo frame
1161	7	Smart thermostat
1162	8	Outdoor picnic set
1163	8	Noise-canceling headphones
1164	8	Adventure book for trip planning
\.

-- Reset sequences to ensure IDs continue correctly
SELECT pg_catalog.setval('public.gift_id_seq', 1164, true);
SELECT pg_catalog.setval('public.person_id_seq', 8, true);
SELECT pg_catalog.setval('public.users_id_seq', 1, true);