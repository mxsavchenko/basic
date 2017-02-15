# -*- coding: utf-8 -*-
# Autor Maxim Savchenko 2017/02/15 v1.1
import os, sys, re, datetime, time
from subprocess import call
###############################
# Путь к файлам с номерами телефонов
file_path = '/var/samba/pbx/'
# Таймаут обработки файлов
timeout = 35
# Путь к каталогу asterisk-outgoing
path = '/tmp/calls/'
# Текущая дата и время
cur_date = datetime.datetime.strptime(datetime.datetime.now().strftime('%y%m%d%H%M.%S'),'%y%m%d%H%M.%S')
# Массив номеров телефонов
list_numbers = []
###############################
all_files = os.listdir(file_path)
if (len(all_files)) > 0:
  for file in all_files:
    if os.access(file_path+str(file), os.F_OK) or os.access(file_path+str(file), os.R_OK):
      if re.search('^H',file):
        call_type = 'obj'
      else:
        call_type = 'obz'
      f = open(file_path+str(file), 'r')
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
      f.close()
      list_numbers = list(set(list_numbers))
      if len(list_numbers) > 0:
        for phone in list_numbers:
          file_name = path+str(phone)
          f = open(file_name, 'w')
          f.write('Channel: SIP/vocaltec/38044'+phone+'\n'+
          'Callerid: 380443793012'+'\n'+
          'MaxRetries: 1'+'\n'+ <------># Количество повторных звонков(если первый раз не дозвонились)
          'RetryTime: 3600'+'\n'+<-----># Через сколько секунд позвонить повторно
          'WaitTime: 35'+'\n'+          # Ожидание вызова (в секундах)
          'Context: '+call_type+'\n'+
          'Extension: s'+'\n'+
          'Priority: 1'+'\n'+
          'Archive: Yes')
          f.close()
          cur_date = cur_date + datetime.timedelta(seconds=timeout)
          new_date = cur_date.strftime('%y%m%d%H%M.%S')
          call(["touch", "-t",new_date, file_name])
      os.unlink(file_path+str(file))
    else:
      print("ERROR: incorrent file or permitions: "+files+str(file))

