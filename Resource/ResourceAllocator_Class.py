#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [ActionTranslator] ActionTranslator class file
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)   
# @version  3_2   
# TEST 2021-11-01
# TEST 2022-04-11
# TEST 2024-06-14

import importlib.util
import os, sys
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def load_classes_from_path(path):
    classes = {}
    
    for filename in os.listdir(path):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]  # .py 확장자 제거
            file_path = os.path.join(path, filename)
            
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 모듈에서 모든 클래스 추출
            for attr_name in dir(module):
                if "Module" in attr_name:
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type):
                        classes[attr_name] = attr
    
    return classes

def create_combined_class(base_class, classes_to_inherit):
    class_name = "ResourceAllocator"
    bases = (base_class, *classes_to_inherit)
    
    def init_combined(self, *args, **kwargs):
        base_class.__init__(self, )
        for cls in classes_to_inherit:
            cls.__init__(self, *args, **kwargs)
    
    new_class = type(class_name, bases, {
        "__init__": init_combined
    })
    
    return new_class

class BaseResourceAllocator:
    """
    ResourceAllocator class read recipe file (json), and allocate & link each task to proper devices
    """

# call class in "Action/Module/{module name}Module.py" path
path_to_classes = "Resource/Module"
loaded_classes_dict = load_classes_from_path(path_to_classes)
loaded_classes = list(loaded_classes_dict.values())

# define ActionTranslator class, inherited all classes of module
ResourceAllocator = create_combined_class(BaseResourceAllocator, loaded_classes)

if __name__=="__main__":

    serverLogger_obj = None  # example
    ResourceManager_obj = None  # example
    schedule_mode = "example_mode"

    dynamic_instance = ResourceAllocator()
    print(dir(dynamic_instance))
