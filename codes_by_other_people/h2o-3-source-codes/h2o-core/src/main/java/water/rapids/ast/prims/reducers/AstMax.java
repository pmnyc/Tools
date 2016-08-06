package water.rapids.ast.prims.reducers;

import water.fvec.Vec;

/**
 */
public class AstMax extends AstRollupOp {
  public String str() {
    return "max";
  }

  public double op(double l, double r) {
    return Math.max(l, r);
  }

  public double rup(Vec vec) {
    return vec.max();
  }
}
