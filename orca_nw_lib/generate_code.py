from itertools import zip_longest
import subprocess
from git import Repo
import shutil,glob,os,ssl,wget
ssl._create_default_https_context = ssl._create_unverified_context

gnmi_proto_dir='./proto'

def compile_gnmi_proto():
    '''
1. wget gnmi.proto and gnmi_ext.proto in predefined directories
2. remove the ./proto directory if it exists
3. execute the command to compile protobufs and generate python in project root directory.
'''
    gnmi_ver = 'v0.9.1'
    gnmi_ext_proto_dir = f'{gnmi_proto_dir}/github.com/openconfig/gnmi/proto/gnmi_ext/'

    gnmi_proto = {f'https://github.com/openconfig/gnmi/raw/{gnmi_ver}/proto/gnmi/gnmi.proto':gnmi_proto_dir,
                f'https://github.com/openconfig/gnmi/raw/{gnmi_ver}/proto/gnmi_ext/gnmi_ext.proto':gnmi_ext_proto_dir}

    shutil.rmtree(gnmi_proto_dir) if os.path.exists(gnmi_proto_dir) else None
    os.makedirs(gnmi_ext_proto_dir, exist_ok=True)
    for proto,dir in gnmi_proto.items():
        wget.download(url=proto, out=dir)


    python_out_dir='./'

    generate_python_cmd = f"python -m grpc_tools.protoc -I{gnmi_proto_dir} -I{gnmi_ext_proto_dir} --python_out={python_out_dir} --pyi_out={python_out_dir}  --grpc_python_out={python_out_dir}  {gnmi_proto_dir}/gnmi.proto {gnmi_ext_proto_dir}/gnmi_ext.proto"
    print(os.popen(generate_python_cmd).read())

openconfig_dir='./openconfig_models'

def compile_openconfig_yang():
    '''
 1. Clone the repository for openconfig models.
2. Move all the yangs at one place under openconfig_dir.
3. Execute the command to genrate python bindings
4. Finally remove everything else than python files.
'''
    shutil.rmtree(openconfig_dir) if os.path.exists(openconfig_dir) else None
    Repo.clone_from('https://github.com/openconfig/public.git', openconfig_dir)

    ## Bring all yang together
    for f1,f2,f3 in zip_longest(glob.glob(f'{openconfig_dir}/release/models/*.yang')
                        ,glob.glob(f'{openconfig_dir}/release/models/*/*.yang')
                        ,glob.glob(f'{openconfig_dir}/third_party/ietf/*.yang')):
        for f in f1,f2,f3:
            if f is not None:
                dst_yang=f'{openconfig_dir}/{os.path.basename(f)}'
                shutil.move(f,dst_yang)

    ## Compile yang
    for item in os.listdir(openconfig_dir):
        file_nname_no_ext=os.path.splitext(os.path.basename(item))[0]
        if item.endswith('.yang'):
            cmd=f'pyang --plugindir ./.venv/lib/python3.10/site-packages/pyangbind/plugin -f pybind -p {openconfig_dir} -o {openconfig_dir}/{file_nname_no_ext}.py {openconfig_dir}/{item}'
            try:
                subprocess.check_output(cmd,shell=True)
            except Exception as e:
                print(f'Exception occurred while processing {item} , {e}')

    ## Cleanup everything except python files

    # TODO following needs to be in sysnch with python generation above, curretly the above commands starts in background, at same time following code starts deleting yang files
    # resultign in errors

    #for item in os.listdir(openconfig_dir):      
    #    if not item.endswith('.py'):
    #        file_to_delete=f'{openconfig_dir}/{item}'
    #        try:
    #            os.remove(file_to_delete)
    #        except PermissionError as e:
    #            print(f'{file_to_delete} couldn\'t be deleted- {e}')

def cleanup_generated_code():
    try:
        print(f'Deleting {openconfig_dir}')
        shutil.rmtree(openconfig_dir)
    except FileNotFoundError as e:
        print(e)
    
    print('Deleting generated gnmi code.')
    
    try:
        shutil.rmtree(gnmi_proto_dir)
    except FileNotFoundError as e:
        print(e)
        
    try:
        shutil.rmtree('./github')
    except FileNotFoundError as e:
        print(e)
        
    try:
        shutil.rmtree('./github.com')
    except FileNotFoundError as e:
        print(e)
        
    fileList = glob.glob('gnmi_pb2*.py*')
    for f in fileList:
        try:
            os.remove(f)
        except Exception as e:
            print(e)
        
    
    
input=input("Compile gnmi(g), openconfig(o) or cleanup(c)? ")

if 'c' in input.lower():
    cleanup_generated_code()

if 'g' in input.lower():
    compile_gnmi_proto()

if 'o' in input.lower():
    compile_openconfig_yang()
    


