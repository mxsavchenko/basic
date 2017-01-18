# -*- coding: utf-8 -*-
# Autor Maxim Savchenko 2017/01/17 v1.1
import os, sys, re, datetime, time
###############################
# Количество потоков
threads = 1
# Таймаут обработки файлов
timeout = 35
# Массив номеров телефонов
list_numbers = []
# Счетчик
list_count=0

file = 'test.txt'
if os.access(file, os.F_OK) or os.access(file, os.R_OK):
    f = open(file, 'r')
    for line in f:
        numbers = line.replace(' ', '').replace('\n','')
        if re.search('^\d{7}$', numbers):
            list_numbers.append(numbers)
        elif re.search(',',numbers):
            numbers = numbers.split(',')
            for number in numbers:
                number =  number.replace(' ', '').replace('\n','')
                if re.search('^\d{7}$', number):
                    list_numbers.append(number)
        list_count+=1
    f.close()
    print("Количество номеров для обзвона: "+str(list_count))
    line_count =0
    if list_count > 0:
        for n in list_numbers:

                cur_date = datetime.datetime.now()
                date_of_file = cur_date.strftime("%y%m%d%H%M.%S")
                print(str(n)+' '+str(date_of_file))

else:
    print("Внимание: возникла ошибка при чтении файла: "+file)


#date_of_create_file=time.strftime('%y%m%d%H%M.%S', time.gmtime(os.path.getmtime('test.txt')))
#print (date_of_create_file)
