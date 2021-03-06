#!/usr/bin/python
# coding=utf-8


import subprocess
import os
import sys
import zipfile
import shutil
import datetime


error_color = "\033[31m"
normal_color = "\033[0m"
file_ext = ('.jar', '.aar', '.dex', '.apk')
dir_excl = ("com.android.tools", "org.jetbrains", "android.test", "androidx.test")


def execute_shell(command_list, cwd, is_shell, verbose):
    if verbose:
        print("> 在 %s 路径下执行命令: " % cwd + ' '.join(command_list) )
        pipe = subprocess.Popen(command_list, cwd=cwd, shell=is_shell)
    else:
        pipe = subprocess.Popen(command_list, cwd=cwd, shell=is_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res = pipe.wait()
    return res


def execute_shell_with_output(command_list, cwd, is_shell, verbose):
    if verbose:
        print("> 在 %s 路径下执行命令: " % cwd + ' '.join(command_list))
        pipe = subprocess.Popen(command_list, cwd=cwd, shell=is_shell, stdout=subprocess.PIPE)
    else:
        pipe = subprocess.Popen(command_list, cwd=cwd, shell=is_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    oc = pipe.communicate()[0]
    return oc


def run_unzip_file(file_path):
    file_name = file_path.split("/")[-1]
    par_dir = os.path.abspath(os.path.join(file_path, os.pardir))
    extract_dir = os.path.join(par_dir, file_name + "_unzip")
    print("run_unzip_file - extract_dir: " + extract_dir)
    if os.path.exists(extract_dir) and os.path.isdir(extract_dir): 
        shutil.rmtree(extract_dir)
    if zipfile.is_zipfile(file_path):
        filezip = zipfile.ZipFile(file_path, 'r')
        filezip.extractall(extract_dir) 
        filezip.close()   
    else:
        print("run_unzip_file - not zip file: " + file_path)
    return extract_dir


def run_scan_file(content, path):
    if os.path.exists(path):
        cmd = ['grep -rn "%s" *' % (content)]
        output = execute_shell_with_output(cmd, path, True, True)
        print(error_color)
        sys.stderr.write(output)
        print(normal_color)
        with open(os.path.join(os.getcwd(), "scan_api_[%s].txt" % (content)), 'a') as f:
            f.write( "Scan Path: %s \n" % (path))
            f.write( "Scan Result: \n" + output)
            f.write( "----------------------------------------------------------------\n\n")
    else:
        print("run_scan_file - not exists file: " + path)    


def run_dex_file(content, path):
    cmd = ['sh d2j-dex2jar.sh -f %s' % (path)]
    cmd_path = os.path.join(os.getcwd(), "dex2jar-2.0")
    res = execute_shell(cmd, cmd_path, True, True)
    if res:
        print("run_dex_file - success")
    else:
        print("run_dex_file - fail dex2jar file: " + path)


def run_aar_file(content, path):
    if os.path.exists(path):
        extract_aar_dir = run_unzip_file(path)
        # print("run_aar_file - unzip: " + extract_aar_dir)
        for file in os.listdir(extract_aar_dir):
            if file.endswith(".jar"):
                file_abs_path = os.path.join(extract_aar_dir, file)
                extract_jar_dir = run_unzip_file(file_abs_path)
                # print("run_aar_file - unzip: " + extract_jar_dir)
                run_scan_file(content, extract_jar_dir)
    else:
        print("run_aar_file - not exists file: " + path) 


def run_jar_file(content, path):
    if os.path.exists(path):
        extract_jar_dir = run_unzip_file(path)
        # print("run_jar_file - unzip: " + extract_jar_dir)
        run_scan_file(content, extract_jar_dir)
    else:
        print("run_jar_file - not exists file: " + path)    


def remove_api_txt_file(content):
    api_txt_file = os.path.join(os.getcwd(), "scan_api_[%s].txt" % (content))
    if os.path.exists(api_txt_file) and os.path.isfile(api_txt_file):
        os.remove(api_txt_file)
        # time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        # backup_file = os.path.join(os.getcwd(), "scan_api_[%s]_%s.txt" % (content, time))
        # os.rename(api_txt_file, backup_file)


def remove_unzip_dir(path):
    if os.path.isdir(path):
        file_list = os.listdir(path)
        for file in file_list:
            file_abs_path = os.path.join(path, file)
            if os.path.isdir(file_abs_path):
                if file_abs_path.endswith("_unzip"):
                    shutil.rmtree(file_abs_path)
                    print("remove_unzip_dir - dir: " + file_abs_path)  
                else:
                    remove_unzip_dir(file_abs_path)
    else:
        unzip_file = os.path.join(path, "_unzip")
        if os.path.exists(unzip_file) and os.path.isdir(unzip_file):
            shutil.rmtree(unzip_file)
            print("remove_unzip_dir - dir: " + unzip_file)  


def execute_scan_dir(content, path):
    if os.path.exists(path):
        file_list = os.listdir(path)
        for file in file_list:
            file_abs_path = os.path.join(path, file)
            if os.path.isfile(file_abs_path):
                if file_abs_path.endswith(file_ext):
                    execute_scan_file(content, file_abs_path)    
            else:
                if not file.startswith(dir_excl):
                    execute_scan_dir(content, file_abs_path)
    else:
        print("execute_scan_dir - not exists dir: " + path)  


def execute_scan_file(content, path):
    if path.endswith(".jar"):
        run_jar_file(content, path)
    elif path.endswith(".aar"):
        run_aar_file(content, path)
    elif path.endswith(".dex") or path.endswith(".apk"):
        run_dex_file(content, path)
    else:
        print("execute_scan_file - not support file: " + path)


def execute_scan_api(content, path):
    print("execute_scan_api - content: %s, path: %s" % (content, path))
    if os.path.exists(path):
        remove_api_txt_file(content)
        if os.path.isdir(path):
            execute_scan_dir(content, path)
        else:
            execute_scan_file(content, path)
        # remove_unzip_dir(path)
    else:
        print("execute_scan_api - not exists path: " + path)  


if __name__ == "__main__":
    if (len(sys.argv) < 3):
        print('usage: ./main.py content("android.support.v7") path(jar, aar, dex, apk)')
        exit(1)
    execute_scan_api(sys.argv[1], sys.argv[2])