# -*- coding: utf-8 -*-

import hashlib


def filtration(spec, objs):
    if spec:
        result = []
        for obj in objs:
            take = True
            for key in spec.keys():
                if key == "or":
                    for k_or in spec[key].keys():
                        take = False
                        if getattr(obj, k_or) == spec[key][k_or]:
                            take = True
                            break
                else:
                    if getattr(obj, key) != spec[key]:
                        take = False
                        break
            if take:
                result.append(obj)
        return result
    else:
        return objs


def calc_ntf_hash(uid1, uid2, meet_id):
    return hashlib.sha1((str(uid1) + str(uid2) + str(meet_id)).encode()).hexdigest()
