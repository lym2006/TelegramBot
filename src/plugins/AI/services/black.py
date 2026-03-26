from ..glo import cupa

def get_black_list():
    path=cupa/'black.txt'
    if not path.exists():
        return []
    with open(path,'r',encoding='utf-8') as a:
        return [line.strip() for line in a if line.strip()]
    
def save_black_list(black_list:list):
    with open(cupa/'black.txt','w',encoding='utf-8') as a:
        a.write('\n'.join(black_list))