//
// Copyright(c) 2022 Intel. Licensed under the MIT License <http://opensource.org/licenses/MIT>.
//

#pragma once

#include <vector>

#include "SimulationController/Rpclib.h"

// enum values must match python/spear/env.py, which is why we write them out explicitly
enum class DataType
{
    Boolean    = 0,
    UInteger8  = 1,
    Integer8   = 2,
    UInteger16 = 3,
    Integer16  = 4,
    UInteger32 = 5,
    Integer32  = 6,
    Float32    = 7,
    Double     = 8,
};
MSGPACK_ADD_ENUM(DataType);

struct Box
{
    double low_;
    double high_;
    std::vector<int64_t> shape_;
    DataType dtype_;

    MSGPACK_DEFINE_MAP(low_, high_, shape_, dtype_);
};
