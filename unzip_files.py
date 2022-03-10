import zipfile
from os import listdir
from os.path import isfile, join, splitext
import concurrent.futures



def unzip_file(file):
    try:
        print(f'Unzinping file: {file}')
        with zipfile.ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall(splitext(file)[0])
        return {'status':'OK', 'file':file}
    except:
        return {'status':'ERRO', 'file':file}

def main():
    onlyfiles = [f for f in listdir('.') if isfile(join('.', f)) and '.zip' in f]
    executor = concurrent.futures.ProcessPoolExecutor(10)
    futures = [executor.submit(unzip_file, file) for file in onlyfiles]
    concurrent.futures.wait(futures)
    results = [future.result() for future in futures]

    for result in results:
        if result['status'] == 'OK':
            with open('done_zip.txt', 'a+') as file:
                file.write(result['file'] + '\r')
        else:
            with open('error_zip.txt', 'a+') as file:
                file.write(result['file'] + '\r')
                
if __name__=="__main__":
    main()